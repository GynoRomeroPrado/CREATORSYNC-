import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, OneToMany } from "typeorm";
import { ObjectType, Field, ID, Int, Float } from "type-graphql";
import { Deal } from "./Deal";

@ObjectType()
@Entity("brands")
export class Brand {
  @Field(() => ID)
  @PrimaryGeneratedColumn()
  id!: number;

  @Field()
  @Column()
  name!: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  website?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  industry?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  logo_url?: string;

  @Field({ nullable: true })
  @Column({ type: "text", nullable: true })
  description?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  contact_email?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  contact_phone?: string;

  @Field({ nullable: true })
  @Column({ nullable: true })
  contact_person?: string;

  @Field(() => Int, { nullable: true })
  @Column({ type: "int", nullable: true })
  company_size?: number;

  @Field({ nullable: true })
  @Column({ nullable: true })
  location?: string;

  @Field(() => Float, { defaultValue: 0 })
  @Column({ type: "float", default: 0 })
  relationship_score!: number;

  @Field()
  @Column({ default: true })
  is_active!: boolean;

  @Field(() => [Deal], { nullable: true })
  @OneToMany(() => Deal, deal => deal.brand)
  deals?: Deal[];

  @Field()
  @CreateDateColumn()
  created_at!: Date;

  @Field()
  @UpdateDateColumn()
  updated_at!: Date;

  @Column({ type: "jsonb", nullable: true })
  metadata?: Record<string, any>;
}
