import { Resolver, Query, Mutation, Arg, Int } from "type-graphql";
import { MediaKit } from "../entities/MediaKit";
import { AppDataSource } from "../data-source";
import { MediaKitGenerator } from "../services/MediaKitGenerator";

@Resolver(MediaKit)
export class MediaKitResolver {
  @Query(() => [MediaKit])
  async mediaKits(
    @Arg("creatorId", () => Int) creatorId: number
  ): Promise<MediaKit[]> {
    const mediaKitRepo = AppDataSource.getRepository(MediaKit);
    return await mediaKitRepo.find({
      where: { creator_id: creatorId },
      order: { created_at: "DESC" }
    });
  }

  @Query(() => MediaKit, { nullable: true })
  async mediaKit(
    @Arg("id", () => Int) id: number
  ): Promise<MediaKit | null> {
    const mediaKitRepo = AppDataSource.getRepository(MediaKit);
    return await mediaKitRepo.findOneBy({ id });
  }

  @Mutation(() => MediaKit)
  async generateMediaKit(
    @Arg("creatorId", () => Int) creatorId: number
  ): Promise<MediaKit> {
    const generator = new MediaKitGenerator();
    return await generator.generateMediaKit(creatorId);
  }

  @Mutation(() => String)
  async exportMediaKitPDF(
    @Arg("id", () => Int) id: number
  ): Promise<string> {
    const generator = new MediaKitGenerator();
    return await generator.exportToPDF(id);
  }

  @Mutation(() => MediaKit)
  async updateMediaKit(
    @Arg("id", () => Int) id: number,
    @Arg("title", { nullable: true }) title?: string,
    @Arg("bio", { nullable: true }) bio?: string
  ): Promise<MediaKit> {
    const mediaKitRepo = AppDataSource.getRepository(MediaKit);

    const mediaKit = await mediaKitRepo.findOneBy({ id });
    if (!mediaKit) throw new Error("Media kit not found");

    if (title) mediaKit.title = title;
    if (bio) mediaKit.bio = bio;

    return await mediaKitRepo.save(mediaKit);
  }
}
