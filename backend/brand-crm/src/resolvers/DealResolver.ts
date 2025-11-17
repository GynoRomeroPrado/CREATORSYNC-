import { Resolver, Query, Mutation, Arg, Int, Float, ObjectType, Field } from "type-graphql";
import { Deal, DealStage, DealStatus } from "../entities/Deal";
import { AppDataSource } from "../data-source";

@Resolver(Deal)
export class DealResolver {
  @Query(() => [Deal])
  async deals(
    @Arg("creatorId", () => Int) creatorId: number,
    @Arg("stage", () => DealStage, { nullable: true }) stage?: DealStage,
    @Arg("status", () => DealStatus, { nullable: true }) status?: DealStatus
  ): Promise<Deal[]> {
    const dealRepo = AppDataSource.getRepository(Deal);

    const query = dealRepo.createQueryBuilder("deal")
      .leftJoinAndSelect("deal.brand", "brand")
      .leftJoinAndSelect("deal.deliverables", "deliverables")
      .where("deal.creator_id = :creatorId", { creatorId });

    if (stage) {
      query.andWhere("deal.stage = :stage", { stage });
    }

    if (status) {
      query.andWhere("deal.status = :status", { status });
    }

    return await query
      .orderBy("deal.created_at", "DESC")
      .getMany();
  }

  @Query(() => Deal, { nullable: true })
  async deal(
    @Arg("id", () => Int) id: number
  ): Promise<Deal | null> {
    const dealRepo = AppDataSource.getRepository(Deal);
    return await dealRepo.findOne({
      where: { id },
      relations: ["brand", "deliverables"]
    });
  }

  @Mutation(() => Deal)
  async createDeal(
    @Arg("creatorId", () => Int) creatorId: number,
    @Arg("brandId", () => Int) brandId: number,
    @Arg("title") title: string,
    @Arg("dealValue", () => Float) dealValue: number,
    @Arg("description", { nullable: true }) description?: string
  ): Promise<Deal> {
    const dealRepo = AppDataSource.getRepository(Deal);

    const deal = dealRepo.create({
      creator_id: creatorId,
      brand_id: brandId,
      title,
      deal_value: dealValue,
      description,
      stage: DealStage.OUTREACH,
      status: DealStatus.ACTIVE,
      probability: 25 // 25% for outreach stage
    });

    return await dealRepo.save(deal);
  }

  @Mutation(() => Deal)
  async updateDealStage(
    @Arg("id", () => Int) id: number,
    @Arg("stage", () => DealStage) stage: DealStage
  ): Promise<Deal> {
    const dealRepo = AppDataSource.getRepository(Deal);

    const deal = await dealRepo.findOneBy({ id });
    if (!deal) throw new Error("Deal not found");

    deal.stage = stage;

    // Update probability based on stage
    const stageProbability: Record<DealStage, number> = {
      [DealStage.OUTREACH]: 25,
      [DealStage.NEGOTIATION]: 50,
      [DealStage.CONTRACT]: 75,
      [DealStage.DELIVERY]: 90,
      [DealStage.PAYMENT]: 95,
      [DealStage.COMPLETED]: 100,
      [DealStage.LOST]: 0
    };

    deal.probability = stageProbability[stage];

    // Mark as won/lost if completed/lost
    if (stage === DealStage.COMPLETED) {
      deal.status = DealStatus.WON;
      deal.actual_close_date = new Date();
    } else if (stage === DealStage.LOST) {
      deal.status = DealStatus.LOST;
    }

    return await dealRepo.save(deal);
  }

  @Mutation(() => Deal)
  async markContractSigned(
    @Arg("id", () => Int) id: number,
    @Arg("signedContractUrl") signedContractUrl: string,
    @Arg("docusignEnvelopeId", { nullable: true }) docusignEnvelopeId?: string
  ): Promise<Deal> {
    const dealRepo = AppDataSource.getRepository(Deal);

    const deal = await dealRepo.findOneBy({ id });
    if (!deal) throw new Error("Deal not found");

    deal.contract_signed = true;
    deal.contract_signed_date = new Date();
    deal.signed_contract_url = signedContractUrl;
    if (docusignEnvelopeId) {
      deal.docusign_envelope_id = docusignEnvelopeId;
    }

    // Move to delivery stage if in contract stage
    if (deal.stage === DealStage.CONTRACT) {
      deal.stage = DealStage.DELIVERY;
      deal.probability = 90;
    }

    return await dealRepo.save(deal);
  }

  @Query(() => DealPipeline)
  async dealPipeline(
    @Arg("creatorId", () => Int) creatorId: number
  ): Promise<DealPipeline> {
    const dealRepo = AppDataSource.getRepository(Deal);

    const deals = await dealRepo.find({
      where: { creator_id: creatorId, status: DealStatus.ACTIVE },
      relations: ["brand"]
    });

    const pipeline: DealPipeline = {
      outreach: deals.filter(d => d.stage === DealStage.OUTREACH),
      negotiation: deals.filter(d => d.stage === DealStage.NEGOTIATION),
      contract: deals.filter(d => d.stage === DealStage.CONTRACT),
      delivery: deals.filter(d => d.stage === DealStage.DELIVERY),
      payment: deals.filter(d => d.stage === DealStage.PAYMENT),
      total_value: deals.reduce((sum, d) => sum + (d.deal_value * (d.probability || 0) / 100), 0),
      deal_count: deals.length
    };

    return pipeline;
  }
}

// Custom type for pipeline view
@ObjectType()
class DealPipeline {
  @Field(() => [Deal])
  outreach!: Deal[];

  @Field(() => [Deal])
  negotiation!: Deal[];

  @Field(() => [Deal])
  contract!: Deal[];

  @Field(() => [Deal])
  delivery!: Deal[];

  @Field(() => [Deal])
  payment!: Deal[];

  @Field(() => Float)
  total_value!: number;

  @Field(() => Int)
  deal_count!: number;
}
