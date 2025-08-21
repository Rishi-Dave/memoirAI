import Foundation
import UIKit

@MainActor
class CreateMemoirViewModel: ObservableObject {
    @Published var selectedImages: [UIImage] = []
    @Published var isCreating = false
    @Published var showSuccess = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var createdEntry: MemoirEntry?  // Add this to store the created memoir
    
    private let apiClient = MemoirAPIClient.shared
    
    func createMemoir(images: [UIImage], userContext: String, tone: MemoirTone) async {
        isCreating = true
        defer { isCreating = false }
        
        do {
            // Capture the created memoir instead of throwing it away
            let createdMemoir = try await apiClient.createMemoir(images: images, userContext: userContext, tone: tone.rawValue)
            
            // Store the created memoir
            createdEntry = createdMemoir
            showSuccess = true
            
            print("✅ Memoir created successfully: \(createdMemoir.title)")
            
        } catch {
            print("❌ CreateMemoirViewModel error: \(error)")
            errorMessage = error.localizedDescription
            showError = true
        }
    }

    func resetForm() {
        selectedImages.removeAll()
        showSuccess = false
        showError = false
        errorMessage = ""
        createdEntry = nil  // Clear the created entry
    }
    
}


