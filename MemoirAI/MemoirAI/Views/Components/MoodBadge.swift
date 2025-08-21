import SwiftUI

struct MoodBadge: View {
    let mood: String
    
    var body: some View {
        Text(mood.capitalized)
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(moodColor.opacity(0.2))
            .foregroundColor(moodColor)
            .cornerRadius(8)
    }
    
    private var moodColor: Color {
        switch mood.lowercased() {
        case "joyful", "excited": return .yellow
        case "peaceful", "grateful": return .green
        case "nostalgic", "reflective": return .blue
        case "adventurous": return .orange
        case "melancholic": return .purple
        default: return .gray
        }
    }
}

#Preview {
    HStack {
        MoodBadge(mood: "joyful")
        MoodBadge(mood: "peaceful")
        MoodBadge(mood: "nostalgic")
        MoodBadge(mood: "adventurous")
        MoodBadge(mood: "melancholic")
    }
}
