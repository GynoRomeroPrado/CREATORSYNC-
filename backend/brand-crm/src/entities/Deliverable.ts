import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from "typeorm";
import { ObjectType, Field, ID, registerEnumType } from "type-graphql";
import { Deal } from "./Deal";

export enum DeliverableType {
  VIDEO = "video",
  POST = "post",
  STORY = "story",
  LIVESTREAM = "livestream",
  ARTICLE = "article",
  OTHER = "other"
}

export enum DeliverableStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  SUBMITTED = "submitted",
  APPROVED = "approved",
  REVISION_NEEDED = "revision_needed",
  COMPLETED = "completed"
}

registerEnumType(DeliverableType, { name: "DeliverableType" });
registerEnumType(DeliverableStatus, { name: "DeliverableStatus" });

@ObjectType()
@Entity("deliverables")
export class Deliverable {
  @Field(() => ID)
  @PrimaryGeneratedColumn()
  id!: number;

  @Field(() => Int)
  @Column()
  deal_id!: number;

  @Field(() => Deal)
  @ManyToOne(() => Deal, deal => deal.deliverables)
  @JoinColumn({ name: "deal_id" })
  deal!: Deal;

  @Field()
  @Column()
  title!: string;

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  description?: string;

  @Field(() => DeliverableType)
  @Column({ type: "varchar" })
  type!: DeliverableType;

  @Field(() => DeliverableStatus)
  @Column({ type: "varchar", default: DeliverableStatus.PENDING })
  status!: DeliverableStatus;

  @Field()
  @Column({ type: "date" })
  due_date!: Date;

  @Field({ nullable: true })
  @Column({ type: "date", nullable: true })
  submitted_date?: Date;

  @Field({ nullable: true })
  @Column({ type: "date", nullable: true })
  approved_date?: Date;

  @Field({ nullable: true })
  @Column({ nullable: true })
  content_url?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  platform_content_id?: string;

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  feedback?: string;

  @Field()
  @CreateDateColumn()
  created_at!: Date;

  @Field()
  @UpdateDateColumn()
  updated_at!: Date;

  @Column({ type: "jsonb", nullable: true })
  metadata?: Record<string, any>;
}
