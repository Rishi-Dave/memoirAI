import SwiftUI

struct EntryDetailView: View {
    @Environment(\.dismiss) var dismiss
    @State var entry: MemoirEntry
    @StateObject private var viewModel = EntryDetailViewModel()
    @State private var showDeleteAlert = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Title and metadata
                    VStack(alignment: .leading, spacing: 8) {
                        Text(entry.title)
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        HStack {
                            Text(formatDate(entry.createdAt))
                                .foregroundColor(.secondary)
                            
                            Spacer()
                            
                            MoodBadge(mood: entry.primaryMood)
                        }
                    }
                    
                    Divider()
                    
                    // Story content
                    Text(entry.storyContent)
                        .font(.body)
                        .lineSpacing(4)
                    
                    // User context if available
                    if !entry.userContext.isEmpty {
                        Divider()
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Context")
                                .font(.headline)
                            
                            Text(entry.userContext)
                                .font(.body)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    // Images section
                    if !entry.images.isEmpty {
                        Divider()
                        
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Images")
                                .font(.headline)
                            
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible())
                            ], spacing: 8) {
                                ForEach(entry.images, id: \.imageId) { image in
                                    AsyncImage(url: URL(string: image.imageUrl)) { image in
                                        image
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                    } placeholder: {
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(Color.gray.opacity(0.3))
                                            .aspectRatio(1, contentMode: .fit)
                                    }
                                    .frame(height: 120)
                                    .clipped()
                                    .cornerRadius(8)
                                }
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task {
                            // FIX: Don't pass inout, instead get the result and update locally
                            let success = await viewModel.toggleFavorite(entryId: entry.entryId, currentStatus: entry.isFavorite)
                            if success {
                                entry.isFavorite.toggle()
                            }
                        }
                    }) {
                        Image(systemName: entry.isFavorite ? "heart.fill" : "heart")
                            .foregroundColor(entry.isFavorite ? .red : .gray)
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Share", action: shareEntry)
                        Button("Delete", role: .destructive) {
                            showDeleteAlert = true
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .alert("Delete Memoir", isPresented: $showDeleteAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Delete", role: .destructive) {
                    Task {
                        let success = await viewModel.deleteEntry(entry.entryId)
                        if success {
                            dismiss()
                        }
                    }
                }
            } message: {
                Text("Are you sure you want to delete this memoir? This action cannot be undone.")
            }
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .full
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        return dateString
    }
    
    private func shareEntry() {
        let text = "\(entry.title)\n\n\(entry.storyContent)"
        let activityVC = UIActivityViewController(activityItems: [text], applicationActivities: nil)
        
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let window = windowScene.windows.first {
            window.rootViewController?.present(activityVC, animated: true)
        }
    }
}
