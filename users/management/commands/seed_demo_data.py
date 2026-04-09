from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from creators.models import CreatorProfile, Service, Work
from demands.models import Demand, DemandComment
from equipment.models import Equipment
from groupbuy.models import GroupBuy, GroupBuyMember
from chat.models import Message


DEMO_PASSWORD = '12345678'


class Command(BaseCommand):
    help = '生成联调用演示数据（用户/作品/需求/报价/设备/拼单/私信）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='先删除 demo_ 开头的历史演示用户及其级联数据，再重新生成',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        if options['reset']:
            deleted_count, _ = User.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(self.style.WARNING(f'已清理旧演示数据（级联删除对象数）：{deleted_count}'))

        users = self._ensure_users(User)
        creators = [users['demo_creator_1'], users['demo_creator_2'], users['demo_creator_3']]
        students = [users['demo_student_1'], users['demo_student_2']]

        profile_count = self._ensure_creator_profiles(creators)
        work_count = self._ensure_works(creators)
        service_count = self._ensure_services(creators)
        demand_count = self._ensure_demands(students, creators)
        bid_count = self._ensure_demand_comments(creators)
        equipment_count = self._ensure_equipment(creators)
        groupbuy_count = self._ensure_groupbuy(students)
        message_count = self._ensure_messages(students, creators)

        self.stdout.write(self.style.SUCCESS('演示数据准备完成。'))
        self.stdout.write(
            '统计: '
            f'用户 {len(users)} 个, '
            f'创作者档案 {profile_count} 个, '
            f'作品 {work_count} 个, '
            f'服务 {service_count} 个, '
            f'需求 {demand_count} 个, '
            f'报价 {bid_count} 个, '
            f'设备帖子 {equipment_count} 个, '
            f'拼单 {groupbuy_count} 个, '
            f'私信 {message_count} 条'
        )
        self.stdout.write('演示账号密码统一为: 12345678')
        self.stdout.write('可用用户名: demo_student_1, demo_student_2, demo_creator_1, demo_creator_2, demo_creator_3')

    def _upsert_user(self, User, username, role, student_id, phone, bio, tags):
        defaults = {
            'role': role,
            'student_id': student_id,
            'phone': phone,
            'bio': bio,
            'tags': tags,
            'is_verified': True,
            'creator_application_status': 'approved' if role == 'creator' else 'not_applied',
            'creator_applied_at': timezone.now() if role == 'creator' else None,
            'is_active_creator': True,
            'is_staff': role == 'admin',
            'is_superuser': False,
            'email': f'{username}@example.com',
        }
        user, _ = User.objects.update_or_create(username=username, defaults=defaults)
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=['password'])
        return user

    def _ensure_users(self, User):
        return {
            'demo_student_1': self._upsert_user(
                User,
                username='demo_student_1',
                role='student',
                student_id='20260001',
                phone='13800000001',
                bio='演示账号：需求方A',
                tags=['毕业照', '人像'],
            ),
            'demo_student_2': self._upsert_user(
                User,
                username='demo_student_2',
                role='student',
                student_id='20260002',
                phone='13800000002',
                bio='演示账号：需求方B',
                tags=['社团活动', '合影'],
            ),
            'demo_creator_1': self._upsert_user(
                User,
                username='demo_creator_1',
                role='creator',
                student_id='20260101',
                phone='13800000101',
                bio='演示账号：创作者A（人像）',
                tags=[1, 101, 301],
            ),
            'demo_creator_2': self._upsert_user(
                User,
                username='demo_creator_2',
                role='creator',
                student_id='20260102',
                phone='13800000102',
                bio='演示账号：创作者B（活动跟拍）',
                tags=[5, 106, 302],
            ),
            'demo_creator_3': self._upsert_user(
                User,
                username='demo_creator_3',
                role='creator',
                student_id='20260103',
                phone='13800000103',
                bio='演示账号：创作者C（修图）',
                tags=[9, 107, 301],
            ),
        }

    def _ensure_creator_profiles(self, creators):
        count = 0
        profile_defaults = {
            creators[0].id: {
                'tags': [1, 101, 204],
                'service_intro': '擅长毕业照和校园人像，可引导动作。',
                'base_price': Decimal('199.00'),
                'price_range': '199-399',
                'camera_model': 'Sony A7M4',
                'can_provide_makeup': True,
                'can_provide_costume': False,
                'completed_orders': 16,
                'average_rating': 4.8,
                'view_count': 328,
            },
            creators[1].id: {
                'tags': [5, 106, 203],
                'service_intro': '擅长活动跟拍和团体照，出片稳定。',
                'base_price': Decimal('299.00'),
                'price_range': '299-599',
                'camera_model': 'Canon R6',
                'can_provide_makeup': False,
                'can_provide_costume': False,
                'completed_orders': 23,
                'average_rating': 4.9,
                'view_count': 412,
            },
            creators[2].id: {
                'tags': [9, 107, 301],
                'service_intro': '可接修图和短视频剪辑，响应快。',
                'base_price': Decimal('149.00'),
                'price_range': '149-299',
                'camera_model': 'Fuji XT30',
                'can_provide_makeup': False,
                'can_provide_costume': False,
                'completed_orders': 11,
                'average_rating': 4.6,
                'view_count': 201,
            },
        }

        for creator in creators:
            CreatorProfile.objects.update_or_create(user=creator, defaults=profile_defaults[creator.id])
            count += 1

        return count

    def _ensure_works(self, creators):
        now = timezone.now()
        samples = [
            {
                'creator': creators[0],
                'title': '樱花季人像样片',
                'description': '光线柔和，适合毕业季。',
                'tags': ['毕业照', '人像'],
                'shooting_time': now - timedelta(days=20),
                'shooting_location': '武汉大学樱园',
                'like_count': 28,
                'view_count': 320,
                'display_order': 0,
            },
            {
                'creator': creators[0],
                'title': '夜景校园写真',
                'description': '提供夜景补光和后期降噪。',
                'tags': ['夜景', '写真'],
                'shooting_time': now - timedelta(days=7),
                'shooting_location': '老图书馆',
                'like_count': 17,
                'view_count': 188,
                'display_order': 1,
            },
            {
                'creator': creators[1],
                'title': '社团活动跟拍合集',
                'description': '全流程活动记录，适合宣传稿。',
                'tags': ['社团活动', '跟拍'],
                'shooting_time': now - timedelta(days=10),
                'shooting_location': '工学部体育馆',
                'like_count': 35,
                'view_count': 420,
                'display_order': 0,
            },
            {
                'creator': creators[2],
                'title': '生活照精修前后对比',
                'description': '可提供肤色校正和细节精修。',
                'tags': ['修图', '精修'],
                'shooting_time': now - timedelta(days=5),
                'shooting_location': '线上交付',
                'like_count': 12,
                'view_count': 140,
                'display_order': 0,
            },
        ]

        count = 0
        for sample in samples:
            Work.objects.update_or_create(
                creator=sample['creator'],
                title=sample['title'],
                defaults={
                    'description': sample['description'],
                    'tags': sample['tags'],
                    'shooting_time': sample['shooting_time'],
                    'shooting_location': sample['shooting_location'],
                    'is_public': True,
                    'like_count': sample['like_count'],
                    'view_count': sample['view_count'],
                    'display_order': sample['display_order'],
                },
            )
            count += 1

        return count

    def _ensure_services(self, creators):
        samples = [
            {
                'creator': creators[0],
                'name': '毕业照约拍',
                'description': '含前期沟通+拍摄+9张精修。',
                'base_price': Decimal('299.00'),
                'price_range': '299-599',
                'estimated_time': '2小时',
                'tags': ['毕业照', '人像'],
                'order_count': 12,
            },
            {
                'creator': creators[1],
                'name': '活动跟拍',
                'description': '适配社团活动与赛事记录。',
                'base_price': Decimal('399.00'),
                'price_range': '399-799',
                'estimated_time': '半天',
                'tags': ['社团活动', '跟拍'],
                'order_count': 15,
            },
            {
                'creator': creators[2],
                'name': '人像精修',
                'description': '可按张计费，24小时内初稿。',
                'base_price': Decimal('30.00'),
                'price_range': '30-80/张',
                'estimated_time': '24小时',
                'tags': ['修图', '精修'],
                'order_count': 18,
            },
        ]

        count = 0
        for sample in samples:
            Service.objects.update_or_create(
                creator=sample['creator'],
                name=sample['name'],
                defaults={
                    'description': sample['description'],
                    'base_price': sample['base_price'],
                    'price_range': sample['price_range'],
                    'estimated_time': sample['estimated_time'],
                    'is_negotiable': True,
                    'is_available': True,
                    'tags': sample['tags'],
                    'order_count': sample['order_count'],
                },
            )
            count += 1

        return count

    def _ensure_demands(self, students, creators):
        now = timezone.now()
        samples = [
            {
                'publisher': students[0],
                'title': '毕业季双人约拍',
                'demand_type': 'photo',
                'description': '希望在樱园拍毕业照，风格自然。',
                'shooting_time': now + timedelta(days=3),
                'location': '武汉大学',
                'campus_location': '樱园',
                'budget': Decimal('300.00'),
                'min_budget': Decimal('200.00'),
                'max_budget': Decimal('400.00'),
                'people_count': 2,
                'status': 'pending',
                'tags': ['毕业照', '人像'],
                'special_topic': '毕业季',
                'reference_images': [
                    '/media/uploads/demands/demo_1.jpg',
                    '/media/uploads/demands/demo_2.jpg',
                ],
                'matched_creator': None,
            },
            {
                'publisher': students[1],
                'title': '社团路演活动跟拍',
                'demand_type': 'photo',
                'description': '需要记录活动全程，含大合影。',
                'shooting_time': now + timedelta(days=5),
                'location': '武汉大学工学部',
                'campus_location': '工程训练中心门口',
                'budget': Decimal('500.00'),
                'min_budget': Decimal('400.00'),
                'max_budget': Decimal('650.00'),
                'people_count': 1,
                'status': 'matched',
                'tags': ['社团活动', '跟拍'],
                'special_topic': None,
                'reference_images': ['/media/uploads/demands/demo_3.jpg'],
                'matched_creator': creators[1],
            },
            {
                'publisher': students[0],
                'title': '证件照精修需求',
                'demand_type': 'retouch',
                'description': '已有原片，需要快速精修。',
                'shooting_time': now + timedelta(days=1),
                'location': '线上',
                'campus_location': None,
                'budget': Decimal('120.00'),
                'min_budget': Decimal('80.00'),
                'max_budget': Decimal('150.00'),
                'people_count': 1,
                'status': 'pending',
                'tags': ['修图', '证件照'],
                'special_topic': '加急单',
                'reference_images': [],
                'matched_creator': None,
            },
        ]

        count = 0
        for sample in samples:
            Demand.objects.update_or_create(
                publisher=sample['publisher'],
                title=sample['title'],
                defaults={
                    'demand_type': sample['demand_type'],
                    'description': sample['description'],
                    'shooting_time': sample['shooting_time'],
                    'location': sample['location'],
                    'campus_location': sample['campus_location'],
                    'budget': sample['budget'],
                    'min_budget': sample['min_budget'],
                    'max_budget': sample['max_budget'],
                    'people_count': sample['people_count'],
                    'status': sample['status'],
                    'tags': sample['tags'],
                    'special_topic': sample['special_topic'],
                    'reference_images': sample['reference_images'],
                    'matched_creator': sample['matched_creator'],
                    'view_count': 0,
                },
            )
            count += 1

        return count

    def _ensure_demand_comments(self, creators):
        demand_1 = Demand.objects.get(title='毕业季双人约拍')
        demand_2 = Demand.objects.get(title='社团路演活动跟拍')
        demand_3 = Demand.objects.get(title='证件照精修需求')

        samples = [
            {
                'demand': demand_1,
                'creator': creators[0],
                'bid_price': Decimal('280.00'),
                'message': '可提供引导拍摄与9张精修。',
                'status': 'pending',
            },
            {
                'demand': demand_2,
                'creator': creators[1],
                'bid_price': Decimal('500.00'),
                'message': '活动全程跟拍，24小时内交预览。',
                'status': 'accepted',
            },
            {
                'demand': demand_2,
                'creator': creators[0],
                'bid_price': Decimal('520.00'),
                'message': '可加拍幕后花絮。',
                'status': 'rejected',
            },
            {
                'demand': demand_3,
                'creator': creators[2],
                'bid_price': Decimal('100.00'),
                'message': '今晚可以交付初稿。',
                'status': 'pending',
            },
        ]

        count = 0
        for sample in samples:
            DemandComment.objects.update_or_create(
                demand=sample['demand'],
                creator=sample['creator'],
                defaults={
                    'bid_price': sample['bid_price'],
                    'message': sample['message'],
                    'status': sample['status'],
                },
            )
            count += 1

        for demand in Demand.objects.filter(title__in=['毕业季双人约拍', '社团路演活动跟拍', '证件照精修需求']):
            demand.comment_count = demand.comments.count()
            demand.save(update_fields=['comment_count'])

        return count

    def _ensure_equipment(self, creators):
        samples = [
            {
                'publisher': creators[0],
                'post_type': 'rent',
                'category': 'camera',
                'device_model': 'Sony A7M4',
                'rent_per_day': Decimal('180.00'),
                'deposit': Decimal('1500.00'),
                'description': '机身+标变镜头，支持校内当面验机。',
            },
            {
                'publisher': creators[1],
                'post_type': 'rent',
                'category': 'drone',
                'device_model': 'DJI Air 3',
                'rent_per_day': Decimal('220.00'),
                'deposit': Decimal('2000.00'),
                'description': '含两块电池，需有基础飞行经验。',
            },
            {
                'publisher': creators[2],
                'post_type': 'lease',
                'category': 'lens',
                'device_model': '85mm F1.8 定焦镜头',
                'rent_per_day': Decimal('60.00'),
                'deposit': None,
                'description': '求租一周，爱惜设备。',
            },
        ]

        count = 0
        for sample in samples:
            Equipment.objects.update_or_create(
                publisher=sample['publisher'],
                device_model=sample['device_model'],
                defaults={
                    'post_type': sample['post_type'],
                    'category': sample['category'],
                    'rent_per_day': sample['rent_per_day'],
                    'deposit': sample['deposit'],
                    'description': sample['description'],
                    'status': 'active',
                },
            )
            count += 1

        return count

    def _ensure_groupbuy(self, students):
        groupbuy, _ = GroupBuy.objects.update_or_create(
            initiator=students[0],
            title='毕业季团拍拼单',
            defaults={
                'description': '再来1人即可开拍，平摊摄影师费用。',
                'target_people_count': 3,
                'cost_per_person': Decimal('199.00'),
                'status': 'recruiting',
            },
        )

        GroupBuyMember.objects.update_or_create(groupbuy=groupbuy, user=students[1])
        return 1

    def _ensure_messages(self, students, creators):
        samples = [
            {
                'sender': students[0],
                'receiver': creators[0],
                'content': '[DEMO] 你好，我想咨询毕业照约拍档期。',
            },
            {
                'sender': creators[0],
                'receiver': students[0],
                'content': '[DEMO] 周六下午有空档，可以先沟通风格。',
            },
            {
                'sender': students[1],
                'receiver': creators[1],
                'content': '[DEMO] 活动跟拍能否提供预览片？',
            },
        ]

        count = 0
        for sample in samples:
            Message.objects.get_or_create(
                sender=sample['sender'],
                receiver=sample['receiver'],
                message_type='private',
                content=sample['content'],
                defaults={'is_read': False},
            )
            count += 1

        return count
