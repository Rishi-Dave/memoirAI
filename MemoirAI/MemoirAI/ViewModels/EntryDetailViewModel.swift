import Foundation

@MainActor
class EntryDetailViewModel: ObservableObject {
    private let apiClient = MemoirAPIClient.shared
    
    // FIX: Return Bool instead of using inout parameter
    func toggleFavorite(entryId: String, currentStatus: Bool) async -> Bool {
        let newFavoriteStatus = !currentStatus
        
        do {
            try await apiClient.toggleFavorite(entryId: entryId, isFavorite: newFavoriteStatus)
            return true
        } catch {
            print("Error toggling favorite: \(error)")
            return false
        }
    }
    
    // FIX: Return Bool to indicate success
    func deleteEntry(_ entryId: String) async -> Bool {
        do {
            try await apiClient.deleteEntry(entryId: entryId)
            return true
        } catch {
            print("Error deleting entry: \(error)")
            return false
        }
    }
}
