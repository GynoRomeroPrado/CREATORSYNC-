import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn, OneToMany } from "typeorm";
import { ObjectType, Field, ID, Float, registerEnumType } from "type-graphql";
import { Brand } from "./Brand";
import { Deliverable } from "./Deliverable";

export enum DealStage {
  OUTREACH = "outreach",
  NEGOTIATION = "negotiation",
  CONTRACT = "contract",
  DELIVERY = "delivery",
  PAYMENT = "payment",
  COMPLETED = "completed",
  LOST = "lost"
}

export enum DealStatus {
  ACTIVE = "active",
  WON = "won",
  LOST = "lost",
  ARCHIVED = "archived"
}

registerEnumType(DealStage, { name: "DealStage" });
registerEnumType(DealStatus, { name: "DealStatus" });

@ObjectType()
@Entity("deals")
export class Deal {
  @Field(() => ID)
  @PrimaryGeneratedColumn()
  id!: number;

  @Field(() => Int)
  @Column()
  creator_id!: number;

  @Field(() => Int)
  @Column()
  brand_id!: number;

  @Field(() => Brand)
  @ManyToOne(() => Brand, brand => brand.deals)
  @JoinColumn({ name: "brand_id" })
  brand!: Brand;

  @Field()
  @Column()
  title!: string;

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  description?: string;

  @Field(() => Float)
  @Column({ type: "float" })
  deal_value!: number;

  @Field()
  @Column({ default: "USD" })
  currency!: string;

  @Field(() => DealStage)
  @Column({ type: "varchar", default: DealStage.OUTREACH })
  stage!: DealStage;

  @Field(() => DealStatus)
  @Column({ type: "varchar", default: DealStatus.ACTIVE })
  status!: DealStatus;

  @Field(() => Float, { nullable: true })
  @Column({ type: "float", nullable: true, default: 0 })
  probability?: number;

  @Field({ nullable: true })
  @Column({ type: "date", nullable: true })
  expected_close_date?: Date;

  @Field({ nullable: true })
  @Column({ type: "date", nullable: true })
  actual_close_date?: Date;

  @Field({ nullable: true })
  @Column({ nullable: true })
  contract_url?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  signed_contract_url?: string;

  @Field()
  @Column({ default: false })
  contract_signed!: boolean;

  @Field({ nullable: true })
  @Column({ type: "date", nullable: true })
  contract_signed_date?: Date;

  @Field({ nullable: true })
  @Column({ nullable: true })
  docusign_envelope_id?: string;

  @Field(() => [Deliverable], { nullable: true })
  @OneToMany(() => Deliverable, deliverable => deliverable.deal)
  deliverables?: Deliverable[];

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  notes?: string;

  @Field()
  @CreateDateColumn()
  created_at!: Date;

  @Field()
  @UpdateDateColumn()
  updated_at!: Date;

  @Column({ type: "jsonb", nullable: true })
  metadata?: Record<string, any>;
}
