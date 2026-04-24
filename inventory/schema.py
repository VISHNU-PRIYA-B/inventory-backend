from inventory.excel_utils import delete_inventory_item
from inventory.excel_utils import update_inventory_item
import graphene
import graphene
from graphene_django import DjangoObjectType
from django.conf import settings
import base64
import os
import uuid
from .excel_utils import append_inventory_item, read_inventory_items,reduce_inventory_quantity
from .models import InventoryRequest
import graphql_jwt
from accounts.schema import UserType
from .models import InventoryRequest, IssuedItem


# ─── Inventory Item (Excel-backed) ───────────────────────────────────────────

class InventoryItemType(graphene.ObjectType):
    item_name = graphene.String()
    size = graphene.String()
    item_type = graphene.String()
    length = graphene.String()
    quantity = graphene.Int()
    location = graphene.String()
    description = graphene.String()
    image_path = graphene.String()


# ─── Inventory Request (DB-backed) ───────────────────────────────────────────

class InventoryRequestType(DjangoObjectType):
    requested_by = graphene.Field(UserType)
    class Meta:
        model = InventoryRequest
        fields = (
            'id', 'category', 'item_name', 'size', 'length',
            'quantity', 'description', 'status', 'created_at',
        )
    def resolve_requested_by(self, info):
        return self.requested_by 

class IssuedItemType(DjangoObjectType):
    issued_to = graphene.Field(UserType)
    class Meta:
        model = IssuedItem
        fields = '__all__'
    def resolve_issued_to(self, info):
        return self.issued_to

# ─── Mutations ────────────────────────────────────────────────────────────────

class AddInventoryItem(graphene.Mutation):
    class Arguments:
        item_name = graphene.String(required=True)
        size = graphene.String(required=True)
        length = graphene.String(required=True)
        department = graphene.String(required=True)  
        item_type = graphene.String(required=True)
        quantity = graphene.Int(required=True)
        location = graphene.String(required=True)
        description = graphene.String(required=False, default_value='')
        image_base64 = graphene.String(required=False, default_value='')

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, department, size, length, item_type, quantity, location, description='', image_base64=''):
        image_path = ''

        if image_base64:
            try:
                if ',' in image_base64:
                    header, b64data = image_base64.split(',', 1)
                    ext = 'png' if 'png' in header else 'jpg'
                else:
                    b64data = image_base64
                    ext = 'jpg'

                image_data = base64.b64decode(b64data)
                filename = f'{uuid.uuid4()}.{ext}'
                file_path = os.path.join(settings.MEDIA_ROOT, 'images', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                image_path = f'/media/images/{filename}'
            except Exception:
                image_path = ''

        append_inventory_item(item_type,item_name, size, length, quantity, location, description, department, image_path)
        return AddInventoryItem(success=True, message='Item added to Excel.')


class CreateInventoryRequest(graphene.Mutation):
    class Arguments:
        category = graphene.String(required=True)
        item_name = graphene.String(required=True)
        department = graphene.String(required=True) 
        size = graphene.String(required=True)
        length = graphene.String(required=True)
        quantity = graphene.Int(required=True)
        description = graphene.String(required=False, default_value='')

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, category, item_name, department, size, length, quantity, description=''):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")

        requested_by = user

        InventoryRequest.objects.create(
            category=category,
            item_name=item_name,
            size=size,
            length=length,
            department=department,
            quantity=quantity,
            description=description,
            requested_by=user,
            status='pending',
        )

        return CreateInventoryRequest(success=True, message='Request submitted successfully.')
class ApproveRequest(graphene.Mutation):
    class Arguments:
        request_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, request_id):
        try:
            req = InventoryRequest.objects.get(id=request_id)
        # REDUCE INVENTORY
            reduce_inventory_quantity(
                item_name=req.item_name,
                quantity_to_reduce=req.quantity,
                department=req.department   
            )
            # save issued  item in db
            IssuedItem.objects.create(
                item_name=req.item_name,
                size=req.size,
                length=req.length,
                quantity=req.quantity,
                issued_to=req.requested_by
            )
            #  NEW: update Excel with user
            update_inventory_item(
                item_name=req.item_name,
                old_size=req.size,
                old_length=req.length,
                department=req.department,
                user=req.requested_by.name   # 👈 ADD THIS
            )

            req.status = 'accepted'
            req.save()
            return ApproveRequest(success=True, message='Request accepted.')
        except InventoryRequest.DoesNotExist:
            return ApproveRequest(success=False, message='Request not found.')


class RejectRequest(graphene.Mutation):
    class Arguments:
        request_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, request_id):
        try:
            req = InventoryRequest.objects.get(id=request_id)
            req.status = 'rejected'
            req.save()
            return RejectRequest(success=True, message='Request rejected.')
        except InventoryRequest.DoesNotExist:
            return RejectRequest(success=False, message='Request not found.')


class UpdateInventoryItem(graphene.Mutation):
    class Arguments:
        item_name = graphene.String(required=True)
        old_size = graphene.String(required=True)     # ✅ ADD
        old_length = graphene.String(required=True)
        department = graphene.String(required=True)

        new_item_name = graphene.String(required=False)
        item_type = graphene.String(required=False)
        size = graphene.String(required=False)
        length = graphene.String(required=False)
        quantity = graphene.Int(required=False)
        location = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, old_size, old_length, department, **kwargs):
        from .excel_utils import update_inventory_item
        update_inventory_item(item_name, old_size, old_length, department, **kwargs)
        return UpdateInventoryItem(success=True, message='Item updated.')


class DeleteInventoryItem(graphene.Mutation):
    class Arguments:
        item_name = graphene.String(required=True)
        department = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, department):
        from .excel_utils import delete_inventory_item
        delete_inventory_item(item_name, department)
        return DeleteInventoryItem(success=True, message='Item deleted.')



# ─── Query ────────────────────────────────────────────────────────────────────

class Query(graphene.ObjectType):
    inventory_items = graphene.List(InventoryItemType)
    inventory_requests = graphene.List(InventoryRequestType)

    def resolve_inventory_items(self, info):
        items = read_inventory_items()
        return [InventoryItemType(**item) for item in items]

    def resolve_inventory_requests(self, info):
        return InventoryRequest.objects.all().order_by('-created_at')

    issued_items = graphene.List(IssuedItemType)

    def resolve_issued_items(self, info):
        return IssuedItem.objects.all().order_by('-issued_at')


# ─── Mutation Root ────────────────────────────────────────────────────────────

class Mutation(graphene.ObjectType):
    add_inventory_item = AddInventoryItem.Field()
    create_inventory_request = CreateInventoryRequest.Field()
    approve_request = ApproveRequest.Field()
    reject_request = RejectRequest.Field()
    update_inventory_item = UpdateInventoryItem.Field()
    delete_inventory_item = DeleteInventoryItem.Field()

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()