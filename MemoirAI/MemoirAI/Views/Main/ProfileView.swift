import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @StateObject private var viewModel = ProfileViewModel()
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Profile Header
                    VStack(spacing: 12) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 80))
                            .foregroundColor(.blue)
                        
                        Text(authManager.currentUser?.email ?? "User")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Member since \(formatJoinDate())")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    // Stats Section
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Statistics")
                            .font(.headline)
                        
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            StatCard(title: "Total Entries", value: "\(viewModel.stats.totalEntries)")
                            StatCard(title: "Avg Words", value: "\(viewModel.stats.avgWordCount)")
                            StatCard(title: "Most Common Mood", value: viewModel.stats.mostCommonMood.capitalized)
                            StatCard(title: "Recent Entries", value: "\(viewModel.stats.recentEntriesCount)")
                        }
                    }
                    
                    Spacer()
                    
                    // App Info
                    VStack(spacing: 8) {
                        Text("MemoirAI v1.0")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("Turn your photos into beautiful stories")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    // Sign Out Button
                    Button("Sign Out") {
                        authManager.signOut()
                    }
                    .foregroundColor(.red)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(10)
                }
                .padding()
            }
            .navigationTitle("Profile")
            .task {
                await viewModel.loadStats()
            }
        }
    }
    
    private func formatJoinDate() -> String {
        guard let user = authManager.currentUser else { return "Unknown" }
        
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        
        if let date = formatter.date(from: user.createdAt) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            return displayFormatter.string(from: date)
        }
        return "Unknown"
    }
}

#Preview {
    ProfileView()
        .environmentObject(AuthenticationManager())
}
