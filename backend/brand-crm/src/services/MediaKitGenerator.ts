import { AppDataSource } from "../data-source";
import { MediaKit } from "../entities/MediaKit";
import axios from "axios";

export class MediaKitGenerator {
  async generateMediaKit(creatorId: number): Promise<MediaKit> {
    const mediaKitRepo = AppDataSource.getRepository(MediaKit);

    // Fetch creator stats from Attribution Engine
    const stats = await this.fetchCreatorStats(creatorId);

    // Fetch recent deals/case studies
    const caseStudies = await this.fetchCaseStudies(creatorId);

    // Create media kit
    const mediaKit = mediaKitRepo.create({
      creator_id: creatorId,
      title: `${stats.creator_name} - Media Kit`,
      bio: stats.bio || "Professional content creator",
      platform_stats: stats.platform_stats,
      case_studies: caseStudies,
      audience_demographics: stats.demographics || [],
      content_categories: stats.categories || [],
      rate_cards: this.generateRateCards(stats.platform_stats)
    });

    return await mediaKitRepo.save(mediaKit);
  }

  private async fetchCreatorStats(creatorId: number): Promise<any> {
    try {
      // This would call the Attribution Engine API
      const attributionApiUrl = process.env.ATTRIBUTION_API_URL || "http://localhost:8001";

      const response = await axios.get(`${attributionApiUrl}/api/v1/creators/${creatorId}`);

      // Transform to media kit format
      return {
        creator_name: response.data.full_name,
        bio: response.data.bio,
        platform_stats: [
          {
            platform: "YouTube",
            followers: 50000,
            avg_views: 10000,
            engagement_rate: 5.2
          },
          {
            platform: "TikTok",
            followers: 100000,
            avg_views: 50000,
            engagement_rate: 8.5
          }
        ],
        demographics: ["18-24: 35%", "25-34: 45%", "35-44: 15%", "45+: 5%"],
        categories: ["Technology", "Lifestyle", "Education"]
      };
    } catch (error) {
      // Return defaults if Attribution Engine unavailable
      return {
        creator_name: "Creator",
        bio: "Professional content creator",
        platform_stats: [],
        demographics: [],
        categories: []
      };
    }
  }

  private async fetchCaseStudies(creatorId: number): Promise<any[]> {
    // Fetch completed deals from database
    const dealRepo = AppDataSource.getRepository("Deal");

    // This would query successful deals and transform to case studies
    return [
      {
        brand: "Example Brand",
        campaign: "Product Launch",
        views: 100000,
        engagement: 8500,
        result: "Increased brand awareness by 45%"
      }
    ];
  }

  private generateRateCards(platformStats: any[]): any[] {
    const rates = [];

    for (const stat of platformStats) {
      // Calculate rate based on followers and engagement
      const baseRate = (stat.followers / 1000) * (stat.engagement_rate / 100);

      rates.push({
        content_type: `${stat.platform} - Dedicated Video`,
        price: Math.round(baseRate * 10),
        currency: "USD",
        description: "60-second dedicated video"
      });

      rates.push({
        content_type: `${stat.platform} - Integration`,
        price: Math.round(baseRate * 5),
        currency: "USD",
        description: "30-second integration in video"
      });
    }

    return rates;
  }

  async exportToPDF(mediaKitId: number): Promise<string> {
    const mediaKitRepo = AppDataSource.getRepository(MediaKit);
    const mediaKit = await mediaKitRepo.findOneBy({ id: mediaKitId });

    if (!mediaKit) throw new Error("Media kit not found");

    // This would generate a PDF using a library like puppeteer or pdfkit
    // For now, return placeholder
    const pdfUrl = `/media-kits/${mediaKitId}.pdf`;

    mediaKit.pdf_url = pdfUrl;
    await mediaKitRepo.save(mediaKit);

    return pdfUrl;
  }
}
