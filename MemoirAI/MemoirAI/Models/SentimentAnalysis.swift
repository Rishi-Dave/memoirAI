import Foundation

struct SentimentAnalysis: Codable {
    let primaryMood: String
    let secondaryMoods: [String]
    let emotionalIntensity: Int
    let themes: [String]
    let overallSentiment: String
    
    enum CodingKeys: String, CodingKey {
        case primaryMood = "primary_mood", secondaryMoods = "secondary_moods"
        case emotionalIntensity = "emotional_intensity", themes
        case overallSentiment = "overall_sentiment"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        primaryMood = try container.decode(String.self, forKey: .primaryMood)
        secondaryMoods = (try? container.decode([String].self, forKey: .secondaryMoods)) ?? []
        themes = (try? container.decode([String].self, forKey: .themes)) ?? []
        overallSentiment = try container.decode(String.self, forKey: .overallSentiment)
        
        // Handle emotionalIntensity as string or int
        if let intensityString = try? container.decode(String.self, forKey: .emotionalIntensity) {
            emotionalIntensity = Int(intensityString) ?? 5
        } else {
            emotionalIntensity = (try? container.decode(Int.self, forKey: .emotionalIntensity)) ?? 5
        }
    }
}
