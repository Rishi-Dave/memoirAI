import Foundation

struct User: Codable {
    let userId: String
    let email: String
    let createdAt: String
    let preferences: UserPreferences
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id", email, createdAt = "created_at", preferences
    }
}

struct UserPreferences: Codable {
    let defaultTone: String
    let privacySettings: String
    let notificationEnabled: Bool
    
    enum CodingKeys: String, CodingKey {
        case defaultTone = "default_tone", privacySettings = "privacy_settings"
        case notificationEnabled = "notification_enabled"
    }
}

struct UserStats: Codable {
    let totalEntries: Int
    let avgWordCount: Int
    let recentEntriesCount: Int
    let mostCommonMood: String
    
    init(totalEntries: Int = 0, avgWordCount: Int = 0, recentEntriesCount: Int = 0, mostCommonMood: String = "neutral") {
        self.totalEntries = totalEntries
        self.avgWordCount = avgWordCount
        self.recentEntriesCount = recentEntriesCount
        self.mostCommonMood = mostCommonMood
    }
    
    enum CodingKeys: String, CodingKey {
        case totalEntries = "total_entries", avgWordCount = "avg_word_count"
        case recentEntriesCount = "recent_entries_count", mostCommonMood = "most_common_mood"
    }
}
