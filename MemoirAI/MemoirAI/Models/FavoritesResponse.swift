import Foundation

// Add these new models to handle the favorites API response format
struct FavoritesApiResponse: Codable {
    let success: Bool
    let data: FavoritesData
    let message: String
}

struct FavoritesData: Codable {
    let count: Int
    let entries: [MemoirEntry]
    let filter: String
    let userId: String
    
    enum CodingKeys: String, CodingKey {
        case count, entries, filter
        case userId = "user_id"
    }
}
