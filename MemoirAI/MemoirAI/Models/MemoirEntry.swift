import Foundation

struct MemoirEntry: Identifiable, Codable {
    let id = UUID()
    let entryId: String
    let title: String
    let storyContent: String
    let userContext: String
    let tone: String
    let images: [MemoirImage]
    let sentimentAnalysis: SentimentAnalysis
    let primaryMood: String
    let wordCount: Int
    let estimatedReadTime: String
    var isFavorite: Bool
    let privacyLevel: String
    let tags: [String]
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case entryId = "entry_id"
        case title, storyContent = "story_content", userContext = "user_context"
        case tone, images, sentimentAnalysis = "sentiment_analysis"
        case primaryMood = "primary_mood", wordCount = "word_count"
        case estimatedReadTime = "estimated_read_time", isFavorite = "is_favorite"
        case privacyLevel = "privacy_level", tags, createdAt = "created_at"
        case updatedAt = "updated_at"
    }
    
    // Regular initializer for manual creation
    init(entryId: String, title: String, storyContent: String, userContext: String, tone: String,
         images: [MemoirImage], sentimentAnalysis: SentimentAnalysis, primaryMood: String,
         wordCount: Int, estimatedReadTime: String, isFavorite: Bool, privacyLevel: String,
         tags: [String], createdAt: String, updatedAt: String) {
        self.entryId = entryId
        self.title = title
        self.storyContent = storyContent
        self.userContext = userContext
        self.tone = tone
        self.images = images
        self.sentimentAnalysis = sentimentAnalysis
        self.primaryMood = primaryMood
        self.wordCount = wordCount
        self.estimatedReadTime = estimatedReadTime
        self.isFavorite = isFavorite
        self.privacyLevel = privacyLevel
        self.tags = tags
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
    
    // Custom decoder for JSON decoding (handles string/int type mismatches)
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        entryId = try container.decode(String.self, forKey: .entryId)
        title = try container.decode(String.self, forKey: .title)
        storyContent = try container.decode(String.self, forKey: .storyContent)
        userContext = try container.decode(String.self, forKey: .userContext)
        tone = try container.decode(String.self, forKey: .tone)
        images = (try? container.decode([MemoirImage].self, forKey: .images)) ?? []
        sentimentAnalysis = try container.decode(SentimentAnalysis.self, forKey: .sentimentAnalysis)
        primaryMood = try container.decode(String.self, forKey: .primaryMood)
        estimatedReadTime = try container.decode(String.self, forKey: .estimatedReadTime)
        isFavorite = try container.decode(Bool.self, forKey: .isFavorite)
        privacyLevel = try container.decode(String.self, forKey: .privacyLevel)
        tags = (try? container.decode([String].self, forKey: .tags)) ?? []
        createdAt = try container.decode(String.self, forKey: .createdAt)
        updatedAt = try container.decode(String.self, forKey: .updatedAt)
        
        // Handle wordCount as string or int
        if let wordCountString = try? container.decode(String.self, forKey: .wordCount) {
            wordCount = Int(wordCountString) ?? 0
        } else {
            wordCount = (try? container.decode(Int.self, forKey: .wordCount)) ?? 0
        }
    }
}

struct MemoirImage: Codable {
    let imageId: String
    let caption: String
    let uploadOrder: Int
    let imageUrl: String
    
    enum CodingKeys: String, CodingKey {
        case imageId = "image_id", caption, uploadOrder = "upload_order"
        case imageUrl = "image_url"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        imageId = try container.decode(String.self, forKey: .imageId)
        caption = try container.decode(String.self, forKey: .caption)
        imageUrl = try container.decode(String.self, forKey: .imageUrl)
        
        // Handle upload_order as any type
        if let orderInt = try? container.decode(Int.self, forKey: .uploadOrder) {
            uploadOrder = orderInt
        } else if let orderString = try? container.decode(String.self, forKey: .uploadOrder) {
            uploadOrder = Int(orderString) ?? 1
        } else {
            uploadOrder = 1 // Default fallback
        }
    }
}
