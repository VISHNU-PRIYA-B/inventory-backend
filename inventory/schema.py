# from pyexpat import model
# # from inventory.excel_utils import delete_inventory_item
# # from inventory.excel_utils import update_inventory_item
# import graphene
# from graphene_django import DjangoObjectType
# from django.conf import settings
# import base64
# import os
# import uuid
# # from .excel_utils import append_inventory_item, read_inventory_items,reduce_inventory_quantity
# from .models import InventoryRequest,InventoryItem
# import graphql_jwt
# from accounts.schema import UserType
# from .models import InventoryRequest, IssuedItem


# # ─── Inventory Item (Excel-backed) ───────────────────────────────────────────

# class InventoryItemType(graphene.ObjectType):
#     # item_name = graphene.String()
#     # size = graphene.String()
#     # item_type = graphene.String()
#     # length = graphene.String()
#     # quantity = graphene.Int()
#     # location = graphene.String()
#     # description = graphene.String()
#     # image_path = graphene.String()
#     class Meta:
#         model = InventoryItem
#         fields = '__all__'


# # ─── Inventory Request (DB-backed) ───────────────────────────────────────────

# class InventoryRequestType(DjangoObjectType):
#     requested_by = graphene.Field(UserType)
#     class Meta:
#         model = InventoryRequest
#         fields = (
#             'id', 'category', 'item_name', 'size', 'length',
#             'quantity', 'description', 'status', 'created_at',
#         )
#     def resolve_requested_by(self, info):
#         return self.requested_by 

# class IssuedItemType(DjangoObjectType):
#     issued_to = graphene.Field(UserType)
#     class Meta:
#         model = IssuedItem
#         fields = '__all__'
#     def resolve_issued_to(self, info):
#         return self.issued_to

# # ─── Mutations ────────────────────────────────────────────────────────────────

# class AddInventoryItem(graphene.Mutation):
#     class Arguments:
#         item_name = graphene.String(required=True)
#         size = graphene.String(required=True)
#         length = graphene.String(required=True)
#         department = graphene.String(required=True)  
#         item_type = graphene.String(required=True)
#         quantity = graphene.Int(required=True)
#         location = graphene.String(required=True)
#         description = graphene.String(required=False, default_value='')
#         image_base64 = graphene.String(required=False, default_value='')

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, item_name, department, size, length, item_type, quantity, location, description='', image_base64=''):
#         image_path = ''

#         if image_base64:
#             try:
#                 if ',' in image_base64:
#                     header, b64data = image_base64.split(',', 1)
#                     ext = 'png' if 'png' in header else 'jpg'
#                 else:
#                     b64data = image_base64
#                     ext = 'jpg'

#                 image_data = base64.b64decode(b64data)
#                 filename = f'{uuid.uuid4()}.{ext}'
#                 file_path = os.path.join(settings.MEDIA_ROOT, 'images', filename)
#                 os.makedirs(os.path.dirname(file_path), exist_ok=True)
#                 with open(file_path, 'wb') as f:
#                     f.write(image_data)
#                 image_path = f'/media/images/{filename}'
#             except Exception:
#                 image_path = ''

#         append_inventory_item(item_type,item_name, size, length, quantity, location, description, department, image_path)
#             # ✅ ALSO SAVE TO DB
#         InventoryItem.objects.create(
#             item_name=item_name,
#             size=size,
#             length=length,
#             quantity=quantity,
#             location=location,
#         )
#         return AddInventoryItem(success=True, message='Item added successfully.')


# class CreateInventoryRequest(graphene.Mutation):
#     class Arguments:
#         category = graphene.String(required=True)
#         item_name = graphene.String(required=True)
#         department = graphene.String(required=True) 
#         size = graphene.String(required=True)
#         length = graphene.String(required=True)
#         quantity = graphene.Int(required=True)
#         description = graphene.String(required=False, default_value='')

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, category, item_name, department, size, length, quantity, description=''):
#         user = info.context.user
#         if user.is_anonymous:
#             raise Exception("Authentication required")

#         requested_by = user

#         InventoryRequest.objects.create(
#             category=category,
#             item_name=item_name,
#             size=size,
#             length=length,
#             department=department,
#             quantity=quantity,
#             description=description,
#             requested_by=user,
#             status='pending',
#         )

#         return CreateInventoryRequest(success=True, message='Request submitted successfully.')
# class ApproveRequest(graphene.Mutation):
#     class Arguments:
#         request_id = graphene.Int(required=True)

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, request_id):
#         try:
#             req = InventoryRequest.objects.get(id=request_id)
#         # REDUCE INVENTORY
#             reduce_inventory_quantity(
#                 item_name=req.item_name,
#                 quantity_to_reduce=req.quantity,
#                 department=req.department   
#             )
#             # save issued  item in db
#             IssuedItem.objects.create(
#                 item_name=req.item_name,
#                 size=req.size,
#                 length=req.length,
#                 quantity=req.quantity,
#                 issued_to=req.requested_by
#             )
#             #  NEW: update Excel with user
#             update_inventory_item(
#                 item_name=req.item_name,
#                 old_size=req.size,
#                 old_length=req.length,
#                 department=req.department,
#                 user=req.requested_by.name   # 👈 ADD THIS
#             )

#             req.status = 'accepted'
#             req.save()
#             return ApproveRequest(success=True, message='Request accepted.')
#         except InventoryRequest.DoesNotExist:
#             return ApproveRequest(success=False, message='Request not found.')


# class RejectRequest(graphene.Mutation):
#     class Arguments:
#         request_id = graphene.Int(required=True)

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, request_id):
#         try:
#             req = InventoryRequest.objects.get(id=request_id)
#             req.status = 'rejected'
#             req.save()
#             return RejectRequest(success=True, message='Request rejected.')
#         except InventoryRequest.DoesNotExist:
#             return RejectRequest(success=False, message='Request not found.')


# class UpdateInventoryItem(graphene.Mutation):
#     class Arguments:
#         item_name = graphene.String(required=True)
#         old_size = graphene.String(required=True)     # ✅ ADD
#         old_length = graphene.String(required=True)
#         department = graphene.String(required=True)

#         new_item_name = graphene.String(required=False)
#         item_type = graphene.String(required=False)
#         size = graphene.String(required=False)
#         length = graphene.String(required=False)
#         quantity = graphene.Int(required=False)
#         location = graphene.String(required=False)

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, item_name, old_size, old_length, department, **kwargs):
#         from .excel_utils import update_inventory_item
#         update_inventory_item(item_name, old_size, old_length, department, **kwargs)
#         return UpdateInventoryItem(success=True, message='Item updated.')


# class DeleteInventoryItem(graphene.Mutation):
#     class Arguments:
#         item_name = graphene.String(required=True)
#         department = graphene.String(required=True)

#     success = graphene.Boolean()
#     message = graphene.String()

#     def mutate(self, info, item_name, department):
#         from .excel_utils import delete_inventory_item
#         delete_inventory_item(item_name, department)
#         return DeleteInventoryItem(success=True, message='Item deleted.')



# # ─── Query ────────────────────────────────────────────────────────────────────

# class Query(graphene.ObjectType):
#     inventory_items = graphene.List(InventoryItemType)
#     inventory_requests = graphene.List(InventoryRequestType)

#     def resolve_inventory_items(self, info):
#         # items = read_inventory_items()
#         # return [InventoryItemType(**item) for item in items]
#         return InventoryItem.objects.all()

#     def resolve_inventory_requests(self, info):
#         return InventoryRequest.objects.all().order_by('-created_at')

#     issued_items = graphene.List(IssuedItemType)

#     def resolve_issued_items(self, info):
#         return IssuedItem.objects.all().order_by('-issued_at')


# # ─── Mutation Root ────────────────────────────────────────────────────────────

# class Mutation(graphene.ObjectType):
#     add_inventory_item = AddInventoryItem.Field()
#     create_inventory_request = CreateInventoryRequest.Field()
#     approve_request = ApproveRequest.Field()
#     reject_request = RejectRequest.Field()
#     update_inventory_item = UpdateInventoryItem.Field()
#     delete_inventory_item = DeleteInventoryItem.Field()

#     token_auth = graphql_jwt.ObtainJSONWebToken.Field()
#     verify_token = graphql_jwt.Verify.Field()
#     refresh_token = graphql_jwt.Refresh.Field()

import graphene
from graphene_django import DjangoObjectType
from django.conf import settings
import base64
import os
import uuid
from .models import InventoryRequest, InventoryItem, IssuedItem, ReturnRequest
import graphql_jwt
from accounts.schema import UserType


# ─── Types ────────────────────────────────────────────────────────────────────

class InventoryItemType(DjangoObjectType):
    class Meta:
        model = InventoryItem
        fields = '__all__'


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


class ReturnRequestType(DjangoObjectType):
    requested_by = graphene.Field(UserType)
    class Meta:
        model = ReturnRequest
        fields = ('id', 'item_name', 'size', 'length', 'department',
                  'quantity', 'status', 'created_at','requested_by')
    def resolve_requested_by(self, info):
        return self.requested_by

# ─── Mutations ────────────────────────────────────────────────────────────────

class AddInventoryItem(graphene.Mutation):
    class Arguments:
        item_name   = graphene.String(required=True)
        size        = graphene.String(required=True)
        length      = graphene.String(required=True)
        department  = graphene.String(required=True)
        item_type   = graphene.String(required=True)
        quantity    = graphene.Int(required=True)
        location    = graphene.String(required=True)
        description = graphene.String(required=False, default_value='')
        image_base64 = graphene.String(required=False, default_value='')

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, department, size, length, item_type,
               quantity, location, description='', image_base64=''):
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

        # ✅ Save to DB only
        InventoryItem.objects.create(
            item_type=item_type,
            item_name=item_name,
            size=size,
            length=length,
            quantity=quantity,
            location=location,
            department=department,
            description=description,
            image_path=image_path,
        )
        return AddInventoryItem(success=True, message='Item added successfully.')


class CreateInventoryRequest(graphene.Mutation):
    class Arguments:
        category    = graphene.String(required=True)
        item_name   = graphene.String(required=True)
        department  = graphene.String(required=True)
        size        = graphene.String(required=True)
        length      = graphene.String(required=True)
        quantity    = graphene.Int(required=True)
        description = graphene.String(required=False, default_value='')

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, category, item_name, department, size, length,
               quantity, description=''):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")

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

            # ✅ Reduce quantity in DB
            try:
                item = InventoryItem.objects.get(
                    item_name__iexact=req.item_name,
                    department__iexact=req.department,
                    size__iexact = req.size,
                    length__iexact = req.length,
                )
                item.quantity = max(0, item.quantity - req.quantity)
                item.save()
            except InventoryItem.DoesNotExist:
                pass

            # ✅ Save issued item in DB
            IssuedItem.objects.create(
                item_name=req.item_name,
                size=req.size,
                length=req.length,
                quantity=req.quantity,
                issued_to=req.requested_by,
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
        item_name     = graphene.String(required=True)
        old_size      = graphene.String(required=True)
        old_length    = graphene.String(required=True)
        department    = graphene.String(required=True)
        new_item_name = graphene.String(required=False)
        item_type     = graphene.String(required=False)
        size          = graphene.String(required=False)
        length        = graphene.String(required=False)
        quantity      = graphene.Int(required=False)
        location      = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, old_size, old_length, department, **kwargs):
        try:
            item = InventoryItem.objects.get(
                item_name__iexact=item_name,
                size__iexact=old_size,
                length__iexact=old_length,
                department__iexact=department,
            )

            old_type = item.item_type
            new_type = kwargs.get('item_type')

            # Update the specific item fields
            if 'new_item_name' in kwargs:
                item.item_name = kwargs['new_item_name']
            if 'item_type' in kwargs:
                item.item_type = kwargs['item_type']
            if 'size' in kwargs:
                item.size = kwargs['size']
            if 'length' in kwargs:
                item.length = kwargs['length']
            if 'quantity' in kwargs:
                item.quantity = kwargs['quantity']
            if 'location' in kwargs:
                item.location = kwargs['location']
            item.save()

            # ✅ If type changed, update ALL rows with same old type in same department
            if new_type and old_type and new_type.strip().lower() != old_type.strip().lower():
                InventoryItem.objects.filter(
                    item_type__iexact=old_type,
                    department__iexact=department,
                ).update(item_type=new_type)

            return UpdateInventoryItem(success=True, message='Item updated.')
        except InventoryItem.DoesNotExist:
            return UpdateInventoryItem(success=False, message='Item not found.')


class DeleteInventoryItem(graphene.Mutation):
    class Arguments:
        item_name  = graphene.String(required=True)
        department = graphene.String(required=True)
        size       = graphene.String(required=True)  
        length     = graphene.String(required=True) 

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, department,size,length,):
        try:
            item = InventoryItem.objects.get(
                item_name__iexact=item_name,
                department__iexact=department,
                size__iexact=size,     
                length__iexact=length, 
            )
            item.delete()
            return DeleteInventoryItem(success=True, message='Item deleted.')
        except InventoryItem.DoesNotExist:
            return DeleteInventoryItem(success=False, message='Item not found.')


# ─── Return Request Mutations ─────────────────────────────────────────────────

class CreateReturnRequest(graphene.Mutation):
    class Arguments:
        item_name  = graphene.String(required=True)
        size       = graphene.String(required=True)
        length     = graphene.String(required=True)
        department = graphene.String(required=False, default_value='')
        quantity   = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_name, size, length, quantity, department=''):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")
        ReturnRequest.objects.create(
            item_name=item_name,
            size=size,
            length=length,
            department=department,
            quantity=quantity,
            requested_by=user,
            status='pending',
        )
        return CreateReturnRequest(success=True, message='Return request submitted.')


class ApproveReturnRequest(graphene.Mutation):
    class Arguments:
        return_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, return_id):
        try:
            ret = ReturnRequest.objects.get(id=return_id)
            # Increase inventory quantity
            try:
                item = InventoryItem.objects.get(
                    item_name__iexact=ret.item_name,
                    size__iexact=ret.size,
                    length__iexact=ret.length,
                )
                item.quantity += ret.quantity
                item.save()
            except InventoryItem.DoesNotExist:
                pass

            try:
                issued = IssuedItem.objects.filter(
                    item_name__iexact=ret.item_name,
                    size__iexact=ret.size,
                    length__iexact=ret.length,
                    issued_to=ret.requested_by,
                ).order_by('-issued_at').first()

                if issued:
                    issued.quantity -= ret.quantity
                    if issued.quantity <= 0:
                        issued.delete()  # remove if fully returned
                    else:
                        issued.save()
            except Exception:
                pass

            ret.status = 'accepted'
            ret.save()
            return ApproveReturnRequest(success=True, message='Return accepted, stock updated.')
        except ReturnRequest.DoesNotExist:
            return ApproveReturnRequest(success=False, message='Return request not found.')


class RejectReturnRequest(graphene.Mutation):
    class Arguments:
        return_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, return_id):
        try:
            ret = ReturnRequest.objects.get(id=return_id)
            ret.status = 'rejected'
            ret.save()
            return RejectReturnRequest(success=True, message='Return rejected.')
        except ReturnRequest.DoesNotExist:
            return RejectReturnRequest(success=False, message='Return request not found.')


# ─── Query ────────────────────────────────────────────────────────────────────

class Query(graphene.ObjectType):
    inventory_items    = graphene.List(InventoryItemType)
    inventory_requests = graphene.List(InventoryRequestType)
    issued_items       = graphene.List(IssuedItemType)
    return_requests    = graphene.List(ReturnRequestType)

    def resolve_inventory_items(self, info):
        return InventoryItem.objects.all()

    def resolve_inventory_requests(self, info):
        return InventoryRequest.objects.all().order_by('-created_at')

    def resolve_issued_items(self, info):
        return IssuedItem.objects.all().order_by('-issued_at')

    def resolve_return_requests(self, info):
        return ReturnRequest.objects.all().order_by('-created_at')


# ─── Mutation Root ────────────────────────────────────────────────────────────

class Mutation(graphene.ObjectType):
    add_inventory_item        = AddInventoryItem.Field()
    create_inventory_request  = CreateInventoryRequest.Field()
    approve_request           = ApproveRequest.Field()
    reject_request            = RejectRequest.Field()
    update_inventory_item     = UpdateInventoryItem.Field()
    delete_inventory_item     = DeleteInventoryItem.Field()
    create_return_request     = CreateReturnRequest.Field()
    approve_return_request    = ApproveReturnRequest.Field()
    reject_return_request     = RejectReturnRequest.Field()

    token_auth    = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token  = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()