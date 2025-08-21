import Foundation

@MainActor
class FavoritesViewModel: ObservableObject {
    @Published var favoriteEntries: [MemoirEntry] = []
    @Published var selectedEntry: MemoirEntry?
    @Published var isLoading = false
    
    private let apiClient = MemoirAPIClient.shared
    
    func loadFavorites() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            favoriteEntries = try await apiClient.getFavoriteEntries()
        } catch {
            print("Error loading favorites: \(error)")
        }
    }
}
