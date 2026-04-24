import graphene
import accounts.schema
import inventory.schema


class Query(accounts.schema.Query, inventory.schema.Query, graphene.ObjectType):
    pass


class Mutation(accounts.schema.Mutation, inventory.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
