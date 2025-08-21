// MARK: - Debug MemoirAPIClient.swift with detailed logging
import Foundation
import UIKit

class MemoirAPIClient {
    static let shared = MemoirAPIClient()
    
    // Your AWS API Gateway URL
    private let baseURL = "https://z9pl12d688.execute-api.us-east-1.amazonaws.com/dev"
    private let session = URLSession.shared
    
    // This will be set after successful login
    private var currentUserId: String = ""
    
    private init() {}
    
    // MARK: - User Management
    func createOrGetUser(email: String) async throws -> User {
        print("🔍 Creating user with email: \(email)")
        print("🔍 API URL: \(baseURL)/users")
        
        guard let url = URL(string: "\(baseURL)/users") else {
            print("❌ Invalid URL: \(baseURL)/users")
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["email": email]
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            print("🔍 Request body: \(body)")
        } catch {
            print("❌ Failed to serialize request body: \(error)")
            throw APIError.encodingError
        }
        
        do {
            let (data, response) = try await session.data(for: request)
            
            // Print raw response for debugging
            if let responseString = String(data: data, encoding: .utf8) {
                print("🔍 Raw response: \(responseString)")
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ Response is not HTTPURLResponse")
                throw APIError.invalidResponse
            }
            
            print("🔍 HTTP Status Code: \(httpResponse.statusCode)")
            print("🔍 Response headers: \(httpResponse.allHeaderFields)")
            
            switch httpResponse.statusCode {
            case 200:
                print("✅ User created successfully")
                do {
                    let createResponse = try JSONDecoder().decode(CreateUserResponse.self, from: data)
                    print("🔍 Decoded response: \(createResponse)")
                    currentUserId = createResponse.userId
                    
                    // Return a mock user for now since we got the user_id
                    return User(
                        userId: createResponse.userId,
                        email: email,
                        createdAt: ISO8601DateFormatter().string(from: Date()),
                        preferences: UserPreferences(
                            defaultTone: "heartwarming",
                            privacySettings: "private",
                            notificationEnabled: true
                        )
                    )
                } catch {
                    print("❌ Failed to decode success response: \(error)")
                    throw APIError.decodingError
                }
                
            case 409:
                print("🔍 User already exists")
                // For now, just return an error since we don't have get-by-email endpoint
                throw APIError.userAlreadyExists
                
            case 400:
                print("❌ Bad request - check your request format")
                throw APIError.badRequest
                
            case 500:
                print("❌ Server error")
                throw APIError.serverError
                
            default:
                print("❌ Unexpected status code: \(httpResponse.statusCode)")
                throw APIError.invalidResponse
            }
            
        } catch {
            if error is APIError {
                throw error
            } else {
                print("❌ Network error: \(error.localizedDescription)")
                throw APIError.networkError(error.localizedDescription)
            }
        }
    }
    
    func getUserStats() async throws -> UserStats {
        guard !currentUserId.isEmpty else {
            print("❌ No current user ID")
            throw APIError.notAuthenticated
        }
        
        print("🔍 Getting stats for user: \(currentUserId)")
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/stats") else {
            throw APIError.invalidURL
        }
        
        do {
            let (data, response) = try await session.data(from: url)
            
            if let responseString = String(data: data, encoding: .utf8) {
                print("🔍 Stats response: \(responseString)")
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                print("❌ Stats request failed")
                throw APIError.invalidResponse
            }
            
            return try JSONDecoder().decode(UserStats.self, from: data)
        } catch {
            print("❌ Stats error: \(error)")
            throw error
        }
    }
    
    // MARK: - Memoir Management
    func createMemoir(images: [UIImage], userContext: String, tone: String) async throws -> MemoirEntry {
        guard !currentUserId.isEmpty else {
            throw APIError.notAuthenticated
        }
        
        print("🔍 Creating memoir for user: \(currentUserId)")
        
        // Process and compress images
        let processedImageData = images.compactMap { image -> Data? in
            // Resize image to reduce size
            let resizedImage = image.resized(to: CGSize(width: 800, height: 800))
            // Compress with lower quality
            return resizedImage?.jpegData(compressionQuality: 0.3)
        }
        
        // Check total size before proceeding
        let totalSize = processedImageData.reduce(0) { $0 + $1.count }
        let totalSizeMB = Double(totalSize) / (1024 * 1024)
        print("🔍 Total image data size: \(String(format: "%.2f", totalSizeMB))MB")
        
        // Check if we're approaching the 10MB limit (leaving room for base64 encoding + other data)
        if totalSize > 7_000_000 { // 7MB limit to account for base64 expansion
            throw APIError.imagesTooLarge
        }
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/entries") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let imageObjects = processedImageData.enumerated().map { index, data in
            return [
                "image_data": data.base64EncodedString(),
                "image_format": "jpeg"
            ]
        }
        
        let body: [String: Any] = [
            "user_id": currentUserId,
            "images": imageObjects,
            "user_context": userContext,
            "tone": tone
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Create memoir response: \(responseString)")
        }
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        let apiResponse = try JSONDecoder().decode(CreateMemoirApiResponse.self, from: data)
        let createResponse = apiResponse.memoir
        
        return MemoirEntry(
            entryId: createResponse.entryId,
            title: createResponse.title,
            storyContent: createResponse.storyContent,
            userContext: userContext,
            tone: tone,
            images: createResponse.images,
            sentimentAnalysis: createResponse.sentimentAnalysis,
            primaryMood: createResponse.sentimentAnalysis.primaryMood,
            wordCount: createResponse.metadata.wordCount,
            estimatedReadTime: createResponse.metadata.createdAt,
            isFavorite: false,
            privacyLevel: "private",
            tags: [],
            createdAt: createResponse.metadata.createdAt,
            updatedAt: createResponse.metadata.createdAt
        )
    }
    func getUserEntries() async throws -> [MemoirEntry] {
        guard !currentUserId.isEmpty else {
            throw APIError.notAuthenticated
        }
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/entries") else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Entries response: \(responseString)")
        }
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        let entriesResponse = try JSONDecoder().decode(EntriesResponse.self, from: data)
        return entriesResponse.entries
    }
    
    func getFavoriteEntries() async throws -> [MemoirEntry] {
        guard !currentUserId.isEmpty else {
            throw APIError.notAuthenticated
        }
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/entries/favorites") else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Raw favorites response:")
            print(responseString)
        }
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        // Decode the actual response format
        let favoritesResponse = try JSONDecoder().decode(FavoritesApiResponse.self, from: data)
        return favoritesResponse.data.entries
    }
    
    func toggleFavorite(entryId: String, isFavorite: Bool) async throws {
        guard !currentUserId.isEmpty else {
            throw APIError.notAuthenticated
        }
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/entries/\(entryId)/favorite") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["is_favorite": isFavorite]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
    }
    
    func deleteEntry(entryId: String) async throws {
        guard !currentUserId.isEmpty else {
            throw APIError.notAuthenticated
        }
        
        guard let url = URL(string: "\(baseURL)/users/\(currentUserId)/entries/\(entryId)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
    }
    
    func signIn(email: String, password: String) async throws -> User {
        guard let url = URL(string: "\(baseURL)/auth/login") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "email": email,
            "password": password
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
            let loginResponse = try JSONDecoder().decode(LoginResponse.self, from: data)
            currentUserId = loginResponse.user.userId
            return loginResponse.user
        } else if httpResponse.statusCode == 401 {
            throw APIError.invalidCredentials
        } else {
            throw APIError.invalidResponse
        }
    }

    func signUp(email: String, password: String) async throws -> User {
        guard let url = URL(string: "\(baseURL)/auth/register") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "email": email,
            "password": password
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
                    let registerResponse = try JSONDecoder().decode(RegisterResponse.self, from: data)
                    // After registration, get full user data
                    currentUserId = registerResponse.userId
                    return try await getUserById(userId: registerResponse.userId)
                } else if httpResponse.statusCode == 409 {
                    throw APIError.userAlreadyExists
                } else {
                    throw APIError.invalidResponse
                }
    }

    func clearCurrentUser() {
        currentUserId = ""
    }

    private func getUserById(userId: String) async throws -> User {
        guard let url = URL(string: "\(baseURL)/users/\(userId)") else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        
        // Create a wrapper model for the response
        struct GetUserResponse: Codable {
            let success: Bool
            let user: User
            let message: String
        }
        
        // Decode the wrapped response and extract the user
        let userResponse = try JSONDecoder().decode(GetUserResponse.self, from: data)
        return userResponse.user
    }
    
}

// MARK: - API Response Models
struct CreateUserResponse: Codable {
    let userId: String
    let email: String
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id", email
    }
}

struct CreateMemoirResponse: Codable {
    let success: Bool
    let entryId: String
    let title: String
    let storyContent: String
    let sentimentAnalysis: SentimentAnalysis
    let images: [MemoirImage]
    let metadata: MemoirMetadata
    
    enum CodingKeys: String, CodingKey {
        case success, entryId = "entry_id", title
        case storyContent = "story_content", sentimentAnalysis = "sentiment_analysis"
        case images, metadata
    }
    
    }

struct MemoirMetadata: Codable {
    let wordCount: Int
    let tone: String
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case wordCount = "word_count", tone, createdAt = "created_at"
    }
}

struct EntriesResponse: Codable {
    let entries: [MemoirEntry]
    let count: Int
}

struct LoginResponse: Codable {
    let success: Bool
    let user: User
    let message: String
}

struct RegisterResponse: Codable {
    let success: Bool
    let userId: String
    let email: String
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success, userId = "user_id", email, message
    }
}



// MARK: - Enhanced API Errors
enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case noData
    case decodingError
    case encodingError
    case networkError(String)
    case notAuthenticated
    case userAlreadyExists
    case userNotFound
    case badRequest
    case serverError
    case invalidCredentials
    case imagesTooLarge

    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .noData:
            return "No data received"
        case .decodingError:
            return "Failed to decode response"
        case .encodingError:
            return "Failed to encode request"
        case .networkError(let message):
            return "Network error: \(message)"
        case .notAuthenticated:
            return "User not authenticated"
        case .userAlreadyExists:
            return "User already exists"
        case .userNotFound:
            return "User not found"
        case .badRequest:
            return "Bad request"
        case .serverError:
            return "Server error"
        case .invalidCredentials:
            return "Invalid email or password"
        case .imagesTooLarge:
            return "Images are too large. Please select fewer or smaller images."
        }
        

    }
}


