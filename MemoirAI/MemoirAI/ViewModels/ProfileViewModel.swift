import Foundation

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var stats = UserStats()
    @Published var isLoading = false
    
    private let apiClient = MemoirAPIClient.shared
    
    func loadStats() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            stats = try await apiClient.getUserStats()
        } catch {
            print("Error loading stats: \(error)")
        }
    }
}
