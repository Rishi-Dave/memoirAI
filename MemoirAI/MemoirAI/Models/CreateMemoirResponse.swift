import Foundation

// Correct model for memoir creation response
struct CreateMemoirApiResponse: Codable {
    let success: Bool
    let memoir: CreateMemoirData
    let message: String
}

struct CreateMemoirData: Codable {
    let entryId: String
    let title: String
    let storyContent: String
    let sentimentAnalysis: SentimentAnalysis
    let images: [MemoirImage]
    let metadata: CreateMemoirMetadata
    
    enum CodingKeys: String, CodingKey {
        case entryId = "entry_id"
        case title
        case storyContent = "story_content"
        case sentimentAnalysis = "sentiment_analysis"
        case images
        case metadata
    }
}

struct CreateMemoirMetadata: Codable {
    let wordCount: Int
    let tone: String
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case wordCount = "word_count"
        case tone
        case createdAt = "created_at"
    }
    
    // Handle word_count as string or int
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        tone = try container.decode(String.self, forKey: .tone)
        createdAt = try container.decode(String.self, forKey: .createdAt)
        
        // Handle wordCount as string or int
        if let wordCountString = try? container.decode(String.self, forKey: .wordCount) {
            wordCount = Int(wordCountString) ?? 0
        } else {
            wordCount = (try? container.decode(Int.self, forKey: .wordCount)) ?? 0
        }
    }
}
