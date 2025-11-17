import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from "typeorm";
import { ObjectType, Field, ID, Int } from "type-graphql";

@ObjectType()
@Entity("media_kits")
export class MediaKit {
  @Field(() => ID)
  @PrimaryGeneratedColumn()
  id!: number;

  @Field(() => Int)
  @Column()
  creator_id!: number;

  @Field()
  @Column()
  title!: string;

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  bio?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  profile_image_url?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  cover_image_url?: string;

  @Field(() => [PlatformStat])
  @Column({ type: "jsonb", default: [] })
  platform_stats!: PlatformStat[];

  @Field(() => [CaseStudy], { nullable: true })
  @Column({ type: "jsonb", nullable: true })
  case_studies?: CaseStudy[];

  @Field(() => [String], { nullable: true })
  @Column({ type: "jsonb", nullable: true })
  audience_demographics?: string[];

  @Field(() => [String], { nullable: true })
  @Column({ type: "jsonb", nullable: true })
  content_categories?: string[];

  @Field(() => [RateCard], { nullable: true })
  @Column({ type: "jsonb", nullable: true })
  rate_cards?: RateCard[];

  @Field({ nullable: true })
  @Column({ nullable: true })
  pdf_url?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  public_url?: string;

  @Field()
  @Column({ default: true })
  is_active!: boolean;

  @Field()
  @CreateDateColumn()
  created_at!: Date;

  @Field()
  @UpdateDateColumn()
  updated_at!: Date;
}

@ObjectType()
export class PlatformStat {
  @Field()
  platform!: string;

  @Field(() => Int)
  followers!: number;

  @Field(() => Int)
  avg_views!: number;

  @Field(() => Float)
  engagement_rate!: number;
}

@ObjectType()
export class CaseStudy {
  @Field()
  brand!: string;

  @Field()
  campaign!: string;

  @Field(() => Int)
  views!: number;

  @Field(() => Int)
  engagement!: number;

  @Field({ nullable: true })
  result?: string;
}

@ObjectType()
export class RateCard {
  @Field()
  content_type!: string;

  @Field(() => Float)
  price!: number;

  @Field()
  currency!: string;

  @Field({ nullable: true })
  description?: string;
}
