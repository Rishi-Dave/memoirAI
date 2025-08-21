import Foundation

@MainActor
class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    
    private let apiClient = MemoirAPIClient.shared
    
    func signIn(email: String, password: String) async throws {
        let user = try await apiClient.signIn(email: email, password: password)
        currentUser = user
        isAuthenticated = true
    }
    
    func signUp(email: String, password: String) async throws {
        let user = try await apiClient.signUp(email: email, password: password)
        currentUser = user
        isAuthenticated = true
    }
    
    func signOut() {
        currentUser = nil
        isAuthenticated = false
        apiClient.clearCurrentUser()
    }
}
