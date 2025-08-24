import SwiftUI

struct EntryCardView: View {
    let entry: MemoirEntry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with title and favorite
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(entry.title.trimmingCharacters(in: CharacterSet(charactersIn: "\"")))
                        .font(.headline)
                        .lineLimit(2)
                    Text(formatDate(entry.createdAt))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if entry.isFavorite {
                    Image(systemName: "heart.fill")
                        .foregroundColor(.red)
                }
                
                MoodBadge(mood: entry.primaryMood)
            }
            
            // Story preview
            Text(entry.storyContent)
                .font(.body)
                .lineLimit(3)
                .foregroundColor(.primary)
            
            // Footer
            HStack {
                Text("\(entry.wordCount) words")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(entry.estimatedReadTime)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 5, x: 0, y: 2)
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}
