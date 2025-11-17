import { Resolver, Query, Mutation, Arg, Int, Ctx } from "type-graphql";
import { Brand } from "../entities/Brand";
import { AppDataSource } from "../data-source";

@Resolver(Brand)
export class BrandResolver {
  @Query(() => [Brand])
  async brands(
    @Arg("creatorId", () => Int) creatorId: number
  ): Promise<Brand[]> {
    const brandRepo = AppDataSource.getRepository(Brand);
    return await brandRepo.find({
      where: { is_active: true },
      relations: ["deals"],
      order: { relationship_score: "DESC" }
    });
  }

  @Query(() => Brand, { nullable: true })
  async brand(
    @Arg("id", () => Int) id: number
  ): Promise<Brand | null> {
    const brandRepo = AppDataSource.getRepository(Brand);
    return await brandRepo.findOne({
      where: { id },
      relations: ["deals"]
    });
  }

  @Mutation(() => Brand)
  async createBrand(
    @Arg("name") name: string,
    @Arg("website", { nullable: true }) website?: string,
    @Arg("industry", { nullable: true }) industry?: string,
    @Arg("contactEmail", { nullable: true }) contactEmail?: string,
    @Arg("contactPerson", { nullable: true }) contactPerson?: string
  ): Promise<Brand> {
    const brandRepo = AppDataSource.getRepository(Brand);

    const brand = brand Repo.create({
      name,
      website,
      industry,
      contact_email: contactEmail,
      contact_person: contactPerson,
      relationship_score: 50 // Default score
    });

    return await brandRepo.save(brand);
  }

  @Mutation(() => Brand)
  async updateBrand(
    @Arg("id", () => Int) id: number,
    @Arg("name", { nullable: true }) name?: string,
    @Arg("relationshipScore", () => Float, { nullable: true }) relationshipScore?: number
  ): Promise<Brand> {
    const brandRepo = AppDataSource.getRepository(Brand);

    const brand = await brandRepo.findOneBy({ id });
    if (!brand) throw new Error("Brand not found");

    if (name) brand.name = name;
    if (relationshipScore !== undefined) brand.relationship_score = relationshipScore;

    return await brandRepo.save(brand);
  }

  @Mutation(() => Boolean)
  async deleteBrand(
    @Arg("id", () => Int) id: number
  ): Promise<boolean> {
    const brandRepo = AppDataSource.getRepository(Brand);

    const brand = await brandRepo.findOneBy({ id });
    if (!brand) return false;

    brand.is_active = false;
    await brandRepo.save(brand);

    return true;
  }
}
