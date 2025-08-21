import SwiftUI

struct FavoritesView: View {
    @StateObject private var viewModel = FavoritesViewModel()
    
    var body: some View {
        NavigationView {
            Group {
                if viewModel.isLoading {
                    LoadingView(message: "Loading favorites...")
                } else if viewModel.favoriteEntries.isEmpty {
                    VStack(spacing: 20) {
                        Image(systemName: "heart")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        
                        Text("No Favorites Yet")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Tap the heart icon on any memoir to add it to your favorites.")
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(viewModel.favoriteEntries) { entry in
                                EntryCardView(entry: entry)
                                    .onTapGesture {
                                        viewModel.selectedEntry = entry
                                    }
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("Favorites")
            .refreshable {
                await viewModel.loadFavorites()
            }
            .task {
                await viewModel.loadFavorites()
            }
            .sheet(item: $viewModel.selectedEntry) { entry in
                EntryDetailView(entry: entry)
            }
        }
    }
}

#Preview {
    FavoritesView()
}
