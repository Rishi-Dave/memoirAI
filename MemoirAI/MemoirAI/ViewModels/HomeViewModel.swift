import Foundation

@MainActor
class HomeViewModel: ObservableObject {
    @Published var entries: [MemoirEntry] = []
    @Published var isLoading = false
    @Published var selectedEntry: MemoirEntry?
    
    private let apiClient = MemoirAPIClient.shared
    
    func loadEntries() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            entries = try await apiClient.getUserEntries()
        } catch {
            print("❌ Error loading entries: \(error)")
        }
    }
    
    // Enhanced function to refresh and auto-show specific entry
    func refreshAndShowEntry(entryId: String) async {
        print("🔍 Refreshing entries and looking for: \(entryId)")
        
        // First refresh the entries list
        await loadEntries()
        
        // Give UI a moment to update
        try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // Find and automatically show the specific entry
        if let entry = entries.first(where: { $0.entryId == entryId }) {
            print("✅ Found entry: \(entry.title)")
            selectedEntry = entry
        } else {
            print("❌ Entry not found in list. Available entries:")
            for entry in entries {
                print("   - \(entry.entryId): \(entry.title)")
            }
        }
    }
}
