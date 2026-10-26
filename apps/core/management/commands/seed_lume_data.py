from django.core.management.base import BaseCommand
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User, CustomerProfile, Address
from apps.catalog.models import Category, Subcategory, Brand, Product, ProductImage, ProductVariant, ProductReview
from apps.orders.models import ShippingMethod, Coupon


class Command(BaseCommand):
    help = 'Seeds authentic LUMÉ luxury catalog, categories, products, coupons, and users from Stitch design.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Beginning LUMÉ luxury database seeding...'))

        # 1. Superuser & Demo User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@lume-beauty.eg',
                'first_name': 'LUMÉ',
                'last_name': 'Concierge',
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '+201000000001',
            }
        )
        if created:
            admin_user.set_password('lume2026!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin (pass: lume2026!)'))

        demo_user, created = User.objects.get_or_create(
            username='nour_almasry',
            defaults={
                'email': 'nour.almasry@lume-client.eg',
                'first_name': 'نور',
                'last_name': 'المصري',
                'phone_number': '+201098765432',
                'is_verified': True,
            }
        )
        if created:
            demo_user.set_password('lume2026!')
            demo_user.save()
            CustomerProfile.objects.create(
                user=demo_user,
                skin_type='combination',
                skin_concerns='نضارة وتوحيد لون البشرة، ترطيب عميق لمقاومة حرارة الصيف',
                loyalty_points=450,
            )
            Address.objects.create(
                user=demo_user,
                full_name='نور المصري',
                phone_number='01098765432',
                governorate='cairo',
                city='حي الزمالك، القاهرة',
                street_address='12 شارع حسن صبري',
                building_number='عمارة دجلة',
                floor_number='الدور 3',
                apartment_number='شقة 5',
                nearest_landmark='بجوار حديقة الأسماك',
                is_default=True,
            )
            self.stdout.write(self.style.SUCCESS('Created demo customer: nour_almasry'))

        # 2. Shipping Methods
        shipping_methods_data = [
            {
                'name_ar': 'توصيل فاخر خلال 24 ساعة (القاهرة الكبرى والجيزة)',
                'name_en': 'Prestige 24h Express Delivery (Greater Cairo & Giza)',
                'code': 'cairo_giza_express',
                'delivery_time_ar': 'خلال 24 ساعة',
                'delivery_time_en': 'Within 24 Hours',
                'cost': Decimal('50.00'),
                'free_threshold': Decimal('800.00'),
            },
            {
                'name_ar': 'شحن سريع للإسكندرية ومحافظات الدلتا والوجه البحري',
                'name_en': 'Express Delivery (Alexandria & Delta Governorates)',
                'code': 'alex_delta_express',
                'delivery_time_ar': 'خلال 48 ساعة',
                'delivery_time_en': 'Within 48 Hours',
                'cost': Decimal('65.00'),
                'free_threshold': Decimal('800.00'),
            },
            {
                'name_ar': 'شحن محافظات الصعيد والقناة والبحر الأحمر',
                'name_en': 'Nationwide Courier (Upper Egypt, Canal & Red Sea)',
                'code': 'upper_egypt_express',
                'delivery_time_ar': '3 إلى 4 أيام عمل',
                'delivery_time_en': '3-4 Business Days',
                'cost': Decimal('80.00'),
                'free_threshold': Decimal('1000.00'),
            },
        ]
        for sm_data in shipping_methods_data:
            ShippingMethod.objects.update_or_create(code=sm_data['code'], defaults=sm_data)
        self.stdout.write(self.style.SUCCESS('Shipping methods seeded.'))

        # 3. Coupons
        coupons_data = [
            {
                'code': 'EGYPTGLOW',
                'description': 'كود دار التحرير الترويجي الحصري - خصم 15% على كامل المقتنيات',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.00'),
                'min_order_value': Decimal('500.00'),
                'is_active': True,
            },
            {
                'code': 'WELCOME15',
                'description': 'قسيمة ترحيب حصرية لعميلات لوميه الجدد - خصم 15%',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.00'),
                'min_order_value': Decimal('400.00'),
                'is_active': True,
            },
            {
                'code': 'LUME20',
                'description': 'خصم العضوية الملكية 20% للطلبات فوق 1,000 ج.م',
                'discount_type': 'percentage',
                'discount_value': Decimal('20.00'),
                'min_order_value': Decimal('1000.00'),
                'is_active': True,
            },
        ]
        for c_data in coupons_data:
            Coupon.objects.update_or_create(code=c_data['code'], defaults=c_data)
        self.stdout.write(self.style.SUCCESS('Coupons seeded.'))

        # 4. Brand
        brand, _ = Brand.objects.get_or_create(
            slug='lume-atelier',
            defaults={
                'name_ar': 'دار لوميه المعملية',
                'name_en': 'LUMÉ Atelier & Laboratoire',
                'description_ar': 'دار تجميل ملكية مصرية تصوغ خلاصات نباتات وادي النيل والواحات في مستحضرات فائقة النقاء.',
                'description_en': 'Prestige Egyptian beauty maison formulating ancient Nile botanical elixirs into refined modern dermatological rituals.',
            }
        )

        # 5. Categories (The 4 Volumes from Stitch Design)
        cat_skincare, _ = Category.objects.update_or_create(
            slug='skincare',
            defaults={
                'name_ar': 'العناية بالبشرة',
                'name_en': 'Skincare',
                'volume_number': 'VOL. I',
                'french_subtitle': 'SOIN DU VISAGE',
                'description_ar': 'سيرومات الترميم باللوتس، مياه ورد الفيوم، ومقشرات الرمل الطبيعية النقية.',
                'description_en': 'Restorative blue lotus serums, Fayoum rose hydrosols, and fine mineral exfoliants.',
                'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDb5qWKXD_5J7BERDQyzyth8G2z9kcS4xh9WbIbbgzNIIdZnTVZlzPQcMpFilQLbGMlAz30XloyfglXmEm4EwP--r4-CIFrdWm8KMoCKG6jVlD_M44rjlTOb7bDPqKSt2Bu_QJffnSDa6u34ewDdbsMWkXkOn_8zmRSrYn93glOaG0hjoLsxYSum6d6sr4G2E76LZzrHHFr4HJN2ou9XTRnl4Z0zBAahB_i4oPheIMUKkBZ5-G89Ps7',
                'is_featured': True,
                'sort_order': 1,
            }
        )
        cat_makeup, _ = Category.objects.update_or_create(
            slug='makeup',
            defaults={
                'name_ar': 'المكياج المخملي',
                'name_en': 'Velvet Makeup',
                'volume_number': 'VOL. II',
                'french_subtitle': 'MAQUILLAGE VELOURS',
                'description_ar': 'أحمر شفاه حريري، بودرة الطمي المعدني، وتألق الشمس الشرقية الدافئة.',
                'description_en': 'Silk bullet lipsticks, mineral clay powders, and radiant Mediterranean sun glow.',
                'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAfzAaxY5WmMM2Gqc-CeVVf4GZvqRt7ci8NP--n790zDSOvAGVgaPNk2v7LKdaZQkzSp47_cyrVTJ5LJiLkgHPqViRnORYYVnp8l14FbiwROGAirVklzH7UCm4Q5ZxIHD8H_yLxb3GkIDeMwG8EdAkI3hHD-I0mC56hOmVf3TLw7WE21u6oeP-7ATg9f-XADTLIE17R2tTlgSSg339vieksDNM4UyN1W9rnKSh-hJE6__LHJYypB_C7',
                'is_featured': True,
                'sort_order': 2,
            }
        )
        cat_perfumes, _ = Category.objects.update_or_create(
            slug='perfumes',
            defaults={
                'name_ar': 'عطور وزيوت نادرة',
                'name_en': 'Haute Parfums',
                'volume_number': 'VOL. III',
                'french_subtitle': 'HAUTE PARFUMERIE',
                'description_ar': 'خلاصات العود المعتق، ياسمين واحة سيوة، وعنبر النيل الفاخر النقي.',
                'description_en': 'Aged agarwood attars, hand-harvested Siwa oasis jasmine, and rare Nile amber.',
                'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBPlp-valHJi-OmKz23_xb3YBRf9j3_EIQL7KJVa7ivgERItuJU0zg0wxAYY4SkAErxGdwia2QOHLwDCBwqts1YkxCdDZDMN0VNrz-wjZ1YsRMgTgBVvhl4gzu_FgOFkueAyGIfY1VI4c_2kCRebLh3S4nO1BP8to_OnproV8nJFNi_-NqUJphp6uG9WPHES7rNJQLsI1tHbXquFPydnmdROys5zyZlvgkgPXNdUv--56a1LIc4_Ojl',
                'is_featured': True,
                'sort_order': 3,
            }
        )
        cat_body, _ = Category.objects.update_or_create(
            slug='body',
            defaults={
                'name_ar': 'طقوس العناية بالجسم',
                'name_en': 'Queen Rituals & Body',
                'volume_number': 'VOL. IV',
                'french_subtitle': 'RITUELS DU CORPS',
                'description_ar': 'زيوت التدليك المعطرة، زبدة الكركديه، وحمام الحليب الملكي لنعومة كليوباترا.',
                'description_en': 'Prestige scented body elixirs, hibiscus butter balms, and royal hydrating milk baths.',
                'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAhv-ndO-MBH29IaW4o4nSk1c6TXf8wgV3J-kHpk1k_YZQIV8CeAWtFiNAq65-puq3HeX9cyyKkBV9qOPO9wRGAyiQxz0nbtlkmSPFjKM4XnsXp79zTG6iJV2r8CA9WIjbzNDJG_MDYVA8yV-RiX9LlTUmdRFVmgR9BsXY6IoTH6_ZQCaBohJ6vEoDDSoHzacPk4eC5LF1ZOvmB-ZyAfyGcEv-L4xnl93BwRU5snr_ISpkfrDCUMCbG',
                'is_featured': True,
                'sort_order': 4,
            }
        )

        sub_serums, _ = Subcategory.objects.get_or_create(
            category=cat_skincare,
            slug='royal-serums',
            defaults={'name_ar': 'السيرومات الملكية', 'name_en': 'Royal Serums', 'sort_order': 1}
        )
        sub_creams, _ = Subcategory.objects.get_or_create(
            category=cat_skincare,
            slug='creams-hydration',
            defaults={'name_ar': 'كريمات الترطيب والترميم', 'name_en': 'Restorative Creams', 'sort_order': 2}
        )
        sub_lips, _ = Subcategory.objects.get_or_create(
            category=cat_makeup,
            slug='lipsticks',
            defaults={'name_ar': 'أحمر الشفاه المخملي', 'name_en': 'Velvet Lipsticks', 'sort_order': 1}
        )
        sub_attars, _ = Subcategory.objects.get_or_create(
            category=cat_perfumes,
            slug='pure-attars',
            defaults={'name_ar': 'الزيوت العطرية النقية', 'name_en': 'Pure Botanical Attars', 'sort_order': 1}
        )
        sub_scrubs, _ = Subcategory.objects.get_or_create(
            category=cat_body,
            slug='body-scrubs',
            defaults={'name_ar': 'مقشرات وبلسم الجسم', 'name_en': 'Scrubs & Body Balms', 'sort_order': 1}
        )

        # 6. Detailed Products
        products_data = [
            {
                'name_ar': 'سيروم الذهب ونبتة اللوتس الأزرق للترميم والتفتيح',
                'name_en': 'Royal Blue Lotus & 24K Gold Cellular Radiance Elixir',
                'slug': 'royal-blue-lotus-24k-gold-serum',
                'category': cat_skincare,
                'subcategory': sub_serums,
                'brand': brand,
                'sku': 'LUM-ELX-001',
                'price': Decimal('680.00'),
                'compare_at_price': Decimal('850.00'),
                'stock': 25,
                'short_description_ar': 'تركيبة مركزة برقائق الذهب عيار 24 ومستخلص زهرة اللوتس النيلية لتجديد مرونة وإشراق البشرة وحمايتها من التلوث.',
                'short_description_en': 'A high-potency restorative elixir infused with 24K gold leaves and concentrated sacred Nile blue lotus extract.',
                'description_ar': 'إكسير استثنائي يعيد إحياء أسرار البرديات الفرعونية القديمة بنقاء معملي فائق. يحتوي على 35% خلاصة مركزة من بتلات اللوتس الأزرق العضوي المقطوفة فجراً من مزارع الدلتا، معززة بذرات الذهب الخالص عيار 24 التي تحفز إنتاج الكولاجين الطبيعي وتمنح البشرة توهجاً نضراً وملمساً حريرياً يدوم طوال اليوم.',
                'editorial_quote_ar': '«لم تكن عناية كليوباترا بالبشرة مجرد روتين، بل طقساً أسطورياً مقدساً يُستحضر فيه أريج وادي النيل لترميم الروح وتفتيح الملامح بنضارة ذهبية باهرة.»',
                'formula_details_ar': 'صيغة سريرية خالية من الزيوت المعدنية، البارابين، والكحول المجفف. تحتوي على ببتيدات حيوية ثلاثية المفعول وحمض الهيالورونيك منخفض الوزن الجزيئي الذي يتغلغل لأعمق طبقات البشرة.',
                'usage_instructions_ar': 'ضعي 3 إلى 4 قطرات صباحاً ومساءً على بشرة نظيفة ومرطبة قليلاً بمياه الورد. دلكي بلطف بحركات دائرية صاعدة حتى تذوب رقائق الذهب بالكامل.',
                'ingredients_ar': 'مستخلص اللوتس الأزرق النيلي (Nymphaea Caerulea)، ذهب نقي عيار 24، سكوالين نباتي من زيتون سيوة، حمض الهيالورونيك، نياسيناميد 5%، فيتامين E الطبيعي، ماء زهر البرتقال.',
                'provenance_origin_ar': 'دلتا النيل: لوتس أزرق عضوي معصور بالتقطير البخاري البارد',
                'provenance_origin_en': 'Nile Delta: Organically cultivated sacred blue lotus steam-distilled at dawn',
                'ministry_registration_code': 'EG-EDA-2024-88',
                'ritual_type': 'radiance',
                'target_skin_type': 'all',
                'is_bestseller': True,
                'is_featured': True,
                'is_new_arrival': False,
                'average_rating': Decimal('4.9'),
                'reviews_count': 320,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuB9KA7DeDrQeLfsqsrid5SOo9WDWcysju125CReDykJXJXII9NMQ0IFacx7JyUxtrg7tCLJmyixkF_e2BfGaPnW_zRLZWPn-slvzMMYVoUFNAz5HZJLm-OFvxzUlpfTUnojpEHzkVDIONThwYUsUfRGvowar13Kx0KuAsweXWqNafGG_1rIfeXuSogaF2cM2dP6N1AB_P1cHMCv-dw4ytN9uPpUQ0dX3TVbvQdk9msSbMKhfftfU4bl',
                        'alt_text_ar': 'زجاجة سيروم اللوتس الأزرق والذهب عيار 24 على حجر الترافرتين',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE FORMULATION',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'زجاجة الإكسير النيلية المصنوعة من الكريستال المصنفر بقطارة ذهبية دقيقة',
                    },
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAHTPCeoiMAJ0XbPOpH1W-nLdPrAyOaJf6ERxZzLvT_kpkkYGgiifxgDBYUeFuujgcesYY9lZK9cuTSCYoKCThxApY4DkcqETOczKm1a0MnjVjQ1w3ICw_u7GgYAAkKlA1bKaFCxl7zaK0HYTnuGOY9CL249GSUfee2TQb5TUbmbT4qjvRnmwevW9KEdLmxrNPT80MGuYd9IAh7KL17AhlCCkk7DAmIr_VeLwpztChS9ClLBXxJ7WgS',
                        'alt_text_ar': 'قوام السيروم الشفاف المتلألئ مع رقائق الذهب عيار 24',
                        'is_primary': False,
                        'plate_indicator': 'PLATE 02 — THE TEXTURE',
                        'plate_tag': 'PL.02',
                        'plate_caption': 'ذوبان رقائق الذهب عيار 24 على البشرة لتمنح توهجاً فورياً',
                    },
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAPvwpJa0fo8Gqbiij3ANItJF-3KbytONGBU9jpeA6VlUbjbYghbOe1T6TC-ETTpsiSC9kJvtOpmSBo9lw-8kuUhipDAxeNDvFNlDo3STHN2jB8wseemxxKV7e9w7FIC9aYiZ9dWYbWRKrpv_8aJ6kqw8lLfIWfh0rA3peYV3-lRPAIYAjgpitlslgSFHU613_5Qg_T-Eg-iM7Mv6dtFwoxwgxLLF_6x-ipQhGqCnTnQkdHhkBrrwxm',
                        'alt_text_ar': 'استخلاص بتلات اللوتس الأزرق النقي',
                        'is_primary': False,
                        'plate_indicator': 'PLATE 03 — BOTANICAL EXTRACTION',
                        'plate_tag': 'PL.03',
                        'plate_caption': 'قطرات اللوتس النقي المقطوف فجراً',
                    },
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBMB7U1wP4s77gGnHwDnYc54up8Br2wUbr0461ka1a5TYEwFrnxEov56LDmVyqFqnRx72FesCqJgTW2THJbhEsYhg-En4CB2oyZdWATUuhTeOainMOlTzAOchFgZCNJcXuDpPca284ztfHdJmVyQD3fGIGa8TZktiXIqgjFGbGy8cAm9pyKuFbMdmAM2Nj79-1VL_NyqlhVp84KbL5l_bWdMGyw1EEljzVez4Nqfwu27suji7EHKzv9',
                        'alt_text_ar': 'التغليف الإهدائي الملكي لدار لوميه',
                        'is_primary': False,
                        'plate_indicator': 'PLATE 04 — ATELIER EMBOSSING',
                        'plate_tag': 'PL.04',
                        'plate_caption': 'التغليف الحرفي الفاخر الممهور بختم الشمع',
                    },
                ],
                'variants': [
                    {
                        'title_ar': '30 مل',
                        'title_en': '30ml',
                        'sku': 'LUM-ELX-001-30',
                        'variant_type': 'size',
                        'volume_ml': 30,
                        'badge_text_ar': 'حجم التجربة',
                        'price': Decimal('450.00'),
                        'compare_at_price': Decimal('520.00'),
                        'is_default': False,
                        'stock': 15,
                    },
                    {
                        'title_ar': '50 مل',
                        'title_en': '50ml',
                        'sku': 'LUM-ELX-001-50',
                        'variant_type': 'size',
                        'volume_ml': 50,
                        'badge_text_ar': 'الحجم المثالي الأكثر طلباً',
                        'price': Decimal('680.00'),
                        'compare_at_price': Decimal('850.00'),
                        'is_default': True,
                        'stock': 25,
                    },
                    {
                        'title_ar': '100 مل جامبو',
                        'title_en': '100ml Jumbo',
                        'sku': 'LUM-ELX-001-100',
                        'variant_type': 'size',
                        'volume_ml': 100,
                        'badge_text_ar': 'الأكثر توفيراً (وفري 210 ج.م)',
                        'price': Decimal('1150.00'),
                        'compare_at_price': Decimal('1360.00'),
                        'is_default': False,
                        'stock': 10,
                    },
                ],
            },
            {
                'name_ar': 'زيت العود والياسمين السيوي المركز (50ml)',
                'name_en': 'Siwa Jasmine & Aged Agarwood Pure Perfume Oil',
                'slug': 'siwa-jasmine-agarwood-perfume-oil',
                'category': cat_perfumes,
                'subcategory': sub_attars,
                'brand': brand,
                'sku': 'LUM-OUD-002',
                'price': Decimal('980.00'),
                'compare_at_price': Decimal('1150.00'),
                'stock': 18,
                'short_description_ar': 'مزيج عطري ساحر من أزهار ياسمين سيوة المقطرة يدوياً مع خشب العود المعتق والبخور الملكي.',
                'short_description_en': 'Handcrafted pure perfume oil marrying wild Siwa oasis jasmine with vintage aged oud.',
                'description_ar': 'سيمفونية عطرية شرقية فاخرة بنسبة تركيز 100% بدون كحول. يتم تقطير أزهار الياسمين البلدي في واحة سيوة يدوياً قبل شروق الشمس للحفاظ على زيوتها الأثيرية النادرة، ثم تُمزج مع خشب العود الهندي المعتق لثبات يدوم أكثر من 48 ساعة على النبض والأقمشة الفاخرة.',
                'editorial_quote_ar': '«عطر يستحضر هيبة قصور الفراعنة ونسمات ليالي الواحة الساحرة تحت ضوء القمر.»',
                'formula_details_ar': 'زيت عطري نقي خالٍ تماماً من الكحول والمذيبات الصناعية، مناسب للبشرة الحساسة والشعر.',
                'usage_instructions_ar': 'ضعي مسحة رقيقة عبر القطارة الزجاجية على أماكن النبض: المعصمين، الرقبة، وخلف الأذنين.',
                'ingredients_ar': 'زيت خشب العود المعتق، مستخلص ياسمين سيوة النقي، عنبر أبيض، مسك الغزال النباتي، خشب الصندل.',
                'provenance_origin_ar': 'واحة سيوة: ياسمين مقطر على البارد مع عود مروكي معتق',
                'provenance_origin_en': 'Siwa Oasis: Cold-extracted night-blooming jasmine blended with aged agarwood',
                'ministry_registration_code': 'EG-EDA-2024-94',
                'ritual_type': 'radiance',
                'target_skin_type': 'all',
                'is_bestseller': True,
                'is_featured': True,
                'is_new_arrival': False,
                'average_rating': Decimal('5.0'),
                'reviews_count': 184,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDDas9Cei6LoZO4gfbqYoINBg3zs1JSEgOBdQQBxkgEkmEr1eBkNCcc7kgwUmQTAqaN0FqXlPdcUogplP78jopkzpgd4EZgfuCtowwzwKdQTfp0WZ-0uMPO7pug-amIS6-G2l65-jneUxMVlyH5L_IFnD3wxrRzMGBrMQdbjZgTlu4frrQYJLkjLsTb2MBeoIXZfrr77hbGcqjLRXj-Z0b1JJwn6EByt5uDgSyGNvLnd623ujtKESgn',
                        'alt_text_ar': 'قارورة زيت العود والياسمين السيوي الفاخرة على حجر ملح سيوة',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE SCENT',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'زيت العود والياسمين السيوي المركز مع قطارة نحاسية عتيقة',
                    }
                ],
                'variants': [],
            },
            {
                'name_ar': 'أحمر شفاه ساتان غني بزبدة الشيا والورد البلدي',
                'name_en': 'Velvet Satin Lipstick with Damask Rose & Shea',
                'slug': 'velvet-satin-lipstick-damask-rose',
                'category': cat_makeup,
                'subcategory': sub_lips,
                'brand': brand,
                'sku': 'LUM-LIP-003',
                'price': Decimal('380.00'),
                'compare_at_price': Decimal('450.00'),
                'stock': 35,
                'short_description_ar': 'لون غني مخملي بلمسة ناعمة ترطب الشفاه وتمنح مظهراً ممتلئاً ومشرقاً طوال اليوم.',
                'short_description_en': 'Rich satin bullet lipstick deeply infused with pure Egyptian rose oil and hydrating botanical shea butter.',
                'description_ar': 'أحمر شفاه كلاسيكي صُمم ليوفر صبغة غنية بتمريرة واحدة مع ترطيب عميق يمنع تشقق الشفاه في الأجواء الحارة. صبغاته المعدنية مستخلصة من خامات الأرض الطبيعية، ومطعمة بزيت الورد البلدي الفيومي وزبدة الشيا العضوية.',
                'editorial_quote_ar': '«لمسة حريرية تعانق الشفاه بدفء ألوان الغروب على شاطئ النيل.»',
                'formula_details_ar': 'تركيبة تدوم حتى 8 ساعات دون جفاف، خالية من الرصاص والمعادن الثقيلة.',
                'usage_instructions_ar': 'مرري القلم مباشرة من المنتصف باتجاه الزوايا الخارجية. استخدمي فرشاة الشفاه لتحديد أكثر دقة.',
                'ingredients_ar': 'زيت الورد البلدي، زبدة الشيا الإفريقية، شمع الكارنوبا العضوي، زيت الجوجوبا، صبغات معدنية نقية.',
                'provenance_origin_ar': 'مزارع الفيوم: زيت الورد البلدي المقطر يدوياً',
                'provenance_origin_en': 'Fayoum Oasis: Hand-picked Damask rose oil and mineral pigments',
                'ministry_registration_code': 'EG-EDA-2024-112',
                'ritual_type': 'radiance',
                'target_skin_type': 'all',
                'is_bestseller': True,
                'is_featured': True,
                'is_new_arrival': False,
                'average_rating': Decimal('4.8'),
                'reviews_count': 412,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBW2tS8OxspkSUaW87EPIE3I9iMH9B8qkmfZOVLVW9LG2YJT1LteWid9iwYikhxJ5B5DITms1dolAz3cS5ekinh2CQCJq1c5sIwscehjrC8PL5ruT9sdbjCDK5BJaHTeSvOQBp0YEF_4-h1Zty7hV2IrsfA9GOO5FsIBbfC7bWRxjQsrt8kJrfrZKlT1-6MlZaSNdkxppSgUYnLUaaUKoX-BPbLrPB0Lu3DS8PdCY5HNGLjOzGarlk0',
                        'alt_text_ar': 'أحمر الشفاه الساتان الفاخر بغلاف ذهبي منقوش',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE COLOR',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'أحمر شفاه ساتان بالورد البلدي في غلاف نحاسي فاخر',
                    }
                ],
                'variants': [
                    {
                        'title_ar': 'درجة الورد البلدي 01 (Damask Rose)',
                        'title_en': 'Damask Rose 01',
                        'sku': 'LUM-LIP-003-01',
                        'variant_type': 'shade',
                        'shade_color_hex': '#94452C',
                        'badge_text_ar': 'الأكثر طلباً بمصر',
                        'price': Decimal('380.00'),
                        'compare_at_price': Decimal('450.00'),
                        'is_default': True,
                        'stock': 20,
                    },
                    {
                        'title_ar': 'درجة طمي النوبة 02 (Nubian Ochre)',
                        'title_en': 'Nubian Ochre 02',
                        'sku': 'LUM-LIP-003-02',
                        'variant_type': 'shade',
                        'shade_color_hex': '#B85D43',
                        'badge_text_ar': 'درجة نيود دافئة',
                        'price': Decimal('380.00'),
                        'compare_at_price': Decimal('450.00'),
                        'is_default': False,
                        'stock': 15,
                    },
                ],
            },
            {
                'name_ar': 'كريم ترطيب مكثف بحمض الهيالورونيك والصبار المصري',
                'name_en': 'Intensive Hydration Cream with Egyptian Aloe & HA',
                'slug': 'intensive-hydration-cream-aloe-hyaluronic',
                'category': cat_skincare,
                'subcategory': sub_creams,
                'brand': brand,
                'sku': 'LUM-CRM-004',
                'price': Decimal('490.00'),
                'compare_at_price': Decimal('580.00'),
                'stock': 28,
                'short_description_ar': 'يهدئ البشرة الجافة والمعرضة لحرارة الجو المصري ويدعم حاجز الحماية الطبيعي لمدة 72 ساعة.',
                'short_description_en': 'Deep barrier repair moisturizer fortified with pure Egyptian aloe vera and multi-molecular hyaluronic acid.',
                'description_ar': 'كريم مخملي فائق الخفة سريع الامتصاص، لا يترك أي أثر دهني حتى في ذروة رطوبة الصيف. يجمع بين خلاصة الصبار الصحراوي المصري المركز بنسبة 40% وحمض الهيالورونيك المركب خماسي الطبقات لحبس الماء داخل خلايا البشرة واستعادة مرونتها.',
                'editorial_quote_ar': '«واحة من الترطيب العميق تحمي البشرة من جفاف أجهزة التكييف وحرارة الشمس.»',
                'formula_details_ar': 'تركيبة تم اختبارها سريرياً ومناسبة للبشرة الحساسة والمعرضة للوردية والاحمرار.',
                'usage_instructions_ar': 'دلكي كمية بحجم حبة البازلاء على الوجه والرقبة صباحاً بعد السيروم، ومساءً كخطوة أخيرة.',
                'ingredients_ar': 'جل صبار نقي، حمض الهيالورونيك خماسي الأوزان، سيراميدات نباتية، بانثينول B5، مستخلص الخيار النيلي.',
                'provenance_origin_ar': 'وادي النيل: صبار عضوي طازج معصور بالبارد',
                'provenance_origin_en': 'Nile Valley: Fresh cold-pressed organic aloe vera',
                'ministry_registration_code': 'EG-EDA-2024-73',
                'ritual_type': 'hydration',
                'target_skin_type': 'dry',
                'is_bestseller': True,
                'is_featured': True,
                'is_new_arrival': False,
                'average_rating': Decimal('4.9'),
                'reviews_count': 250,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBVQPkM3UlCQXYdXNtZDpYb9GRNMxUjJ6B64dIcxWYZrFyPG1aWQrSG0IbX-NZaGNP4e4fHQTD0P7pbpWggl9fZWwZ7BIaQZGP3t0GR8c1XqGf4TiXGYTKss3WdL75mMCZDIbZm3-dWGSBmy9wGMnQ0YKu7uTiSuqOkw9PiGsG9CbBIMvLK_chiFcqoYrhh3J5X0y-qN5tdJxabZbct8GL5veb5XJs2drHeK1yceQR2fITMyXof1g0N',
                        'alt_text_ar': 'عبوة كريم الترطيب المكثف السيراميكية الفاخرة',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE BALM',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'كريم ترطيب مكثف بالصبار والهيالورونيك 72 ساعة ترطيب',
                    }
                ],
                'variants': [],
            },
            {
                'name_ar': 'مقشر الكركديه وطمي النوبة البركاني لنضارة الجسم',
                'name_en': 'Aswan Hibiscus & Nubian Volcanic Body Polish',
                'slug': 'aswan-hibiscus-nubian-body-polish',
                'category': cat_body,
                'subcategory': sub_scrubs,
                'brand': brand,
                'sku': 'LUM-SCR-005',
                'price': Decimal('340.00'),
                'compare_at_price': Decimal('420.00'),
                'stock': 22,
                'short_description_ar': 'مقشر علاجي فاخر يزيل الخلايا الميتة ويوحد لون بشرة الجسم بأحماض الكركديه العضوية.',
                'short_description_en': 'Exfoliating botanical body polish combining Aswan hibiscus flower AHA acids with fine mineral Nubian clay.',
                'description_ar': 'طقس سنفرة مستوحى من حمامات النوبة الملكية. يحتوي على حبيبات ملح البحر الأحمر الدقيقة المشبعة بزبدة الشيا وأحماض الكركديه الطبيعية (AHA) التي تقشر بلطف وتزيل التصبغات وتترك البشرة ناعمة كالحرير برائحة وردية منعشة.',
                'editorial_quote_ar': '«طقس التجدد الملكي الذي يمنح الجسم نعومة مخملية وإشراقة وردية فورية.»',
                'formula_details_ar': 'حبيبات تقشير طبيعية 100% تتحول إلى حليب مرطب عند ملامستها للماء أثناء الاستحمام.',
                'usage_instructions_ar': 'دلكي على بشرة رطبة بحركات دائرية لمدة 3-5 دقائق، مع التركيز على الكوعين والركبتين، ثم اشطفي بالماء الدافئ.',
                'ingredients_ar': 'بلورات ملح البحر الأحمر، مسحوق زهور الكركديه الأسواني، طمي النوبة الوردي، زيت اللوز الحلو، زبدة الكاكاو.',
                'provenance_origin_ar': 'أسوان: مستخلص الكركديه العضوي وطمي النوبة',
                'provenance_origin_en': 'Aswan: Organic hibiscus flower extracts and pure Nubian clay',
                'ministry_registration_code': 'EG-EDA-2024-52',
                'ritual_type': 'radiance',
                'target_skin_type': 'all',
                'is_bestseller': False,
                'is_featured': True,
                'is_new_arrival': True,
                'average_rating': Decimal('4.8'),
                'reviews_count': 96,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAhv-ndO-MBH29IaW4o4nSk1c6TXf8wgV3J-kHpk1k_YZQIV8CeAWtFiNAq65-puq3HeX9cyyKkBV9qOPO9wRGAyiQxz0nbtlkmSPFjKM4XnsXp79zTG6iJV2r8CA9WIjbzNDJG_MDYVA8yV-RiX9LlTUmdRFVmgR9BsXY6IoTH6_ZQCaBohJ6vEoDDSoHzacPk4eC5LF1ZOvmB-ZyAfyGcEv-L4xnl93BwRU5snr_ISpkfrDCUMCbG',
                        'alt_text_ar': 'مقشر الكركديه وطمي النوبة مع حبيبات الملح العطري',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE POLISH',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'مقشر الكركديه الأسواني الملكي لنعومة فائقة',
                    }
                ],
                'variants': [],
            },
            {
                'name_ar': 'بخاخ العطر المركز للحقيبة (10ml)',
                'name_en': 'Pocket Travel Scent Mist Spray (10ml)',
                'slug': 'pocket-travel-scent-mist-10ml',
                'category': cat_perfumes,
                'subcategory': sub_attars,
                'brand': brand,
                'sku': 'LUM-TRV-006',
                'price': Decimal('140.00'),
                'compare_at_price': Decimal('180.00'),
                'stock': 40,
                'short_description_ar': 'إصدار الحقيبة الأنيق المكمّل لطقس العطور أثناء التنقل.',
                'short_description_en': 'Sleek travel atomizer bottle infused with blooming Nile orange blossoms and amber.',
                'description_ar': 'بخاخ عطري مصغر بحجم مثالي للحقيبة اليدوية، مصنوع من الألومنيوم المؤكسد بلون التراكوتا الوردي لإنعاش عطركِ في أي لحظة.',
                'editorial_quote_ar': '«رفيقكِ الدائم لحضور ساحر لا يغيب طوال اليوم.»',
                'formula_details_ar': 'تركيبة مركزة خالية من البقع وتدوم حتى 12 ساعة.',
                'usage_instructions_ar': 'رشي رذاذاً خفيفاً على المعصمين والملابس كلما رغبتِ في تجديد أريجكِ.',
                'ingredients_ar': 'ماء زهر البرتقال النيلي، عنبر دافئ، خشب الأرز، مسك أبيض نقي.',
                'provenance_origin_ar': 'القاهرة: عبوة سفر فاخرة مصنعة حصرياً لدار لوميه',
                'provenance_origin_en': 'Cairo: Atelier travel edition refillable atomizer',
                'ministry_registration_code': 'EG-EDA-2024-105',
                'ritual_type': 'radiance',
                'target_skin_type': 'all',
                'is_bestseller': False,
                'is_featured': False,
                'is_new_arrival': True,
                'average_rating': Decimal('4.7'),
                'reviews_count': 82,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuC32-q7Wc0sSojgy8WDN97VGDCh7QN1f_gaL_vW9EIp4-J6BVzIiX7D53GcjUT-ZYx_wzxK4T8H3J6G3gD9ZEtBAKguta_RyNFtDcZahO4hZ9Zgps5mxVrlOEyFrAodUYpOF-8IbZ6r8Op8f5s-C-4UHWZmSEnJhEq0R2ouIvYnc6YzlhcZHPAwWqL8YArjpEntwjmTSU3MWtkUJc6Y0oI1uMfNjY0NCkOyFnJPXINlBxIY00fk-RcB',
                        'alt_text_ar': 'بخاخ العطر المركز للحقيبة بحجم 10 مل',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE POCKET FLACON',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'بخاخ الحقيبة الأنيق',
                    }
                ],
                'variants': [],
            },
            {
                'name_ar': 'وسائد قطن مصري عضوي لإزالة المكياج (80 قطعة)',
                'name_en': 'Organic Egyptian Cotton Luxury Cleansing Pads',
                'slug': 'organic-egyptian-cotton-cleansing-pads',
                'category': cat_skincare,
                'subcategory': sub_creams,
                'brand': brand,
                'sku': 'LUM-COT-007',
                'price': Decimal('85.00'),
                'compare_at_price': Decimal('110.00'),
                'stock': 50,
                'short_description_ar': 'قطن مصري طويل التيلة 100% فائق النعومة وخالٍ من الكيماويات والمبيضات.',
                'short_description_en': '100% long-staple certified Egyptian organic cotton pads crafted for sensitive facial care.',
                'description_ar': 'وسائد قطنية دائرية محاكة من أجود خيوط القطن المصري طويل التيلة المعتمد عضوياً. توفر ملمساً حريرياً لطيفاً على منطقة العينين الحساسة دون أن تتفتت أو تترك أي نسالة.',
                'editorial_quote_ar': '«لمسة النعومة الأسطورية للقطن المصري الأصيل.»',
                'formula_details_ar': 'غير مبيضة بالكلور، قابلة للتحلل الحيوي بالكامل، وصديقة للبيئة.',
                'usage_instructions_ar': 'بللي الوسادة بمياه الورد أو مزيل المكياج وامسحي الوجه بلطف.',
                'ingredients_ar': 'قطن مصري عضوي نقي 100%.',
                'provenance_origin_ar': 'كفر الدوار: قطن مصري طويل التيلة فائق الجودة',
                'provenance_origin_en': 'Kafr El Dawar: 100% Giza long-staple organic cotton',
                'ministry_registration_code': 'EG-EDA-2024-12',
                'ritual_type': 'soothing',
                'target_skin_type': 'sensitive',
                'is_bestseller': False,
                'is_featured': False,
                'is_new_arrival': False,
                'average_rating': Decimal('4.9'),
                'reviews_count': 115,
                'images': [
                    {
                        'image': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAjzHcSEn79ya8afiZ3rlFgXMk7ice4FwJX0NP8b6XsbgF13vyIVV5tFyz35lFjnLqMSSiVdLWiedDXEjhWFoOCEXnNRQVS5HrVTEoSbd1ku4sfg6b6UO1hp73U9_7d_pv_AYLOhlTrnWwoBlmqpGjkB-EfR6lUp_nyMWqLqMsfC4bnG2qM4X21tnLILJngWZA4p2rU11beWMNUF-Jm3rarrHt2B0esdmJz33hgCaDO1XtjRqAih9bN',
                        'alt_text_ar': 'وسائد القطن المصري العضوي في سلة القش الطبيعي',
                        'is_primary': True,
                        'plate_indicator': 'PLATE 01 — THE COTTON',
                        'plate_tag': 'PL.01',
                        'plate_caption': 'قطن مصري طويل التيلة فائق النعومة',
                    }
                ],
                'variants': [],
            },
        ]

        for p_info in products_data:
            images = p_info.pop('images', [])
            variants = p_info.pop('variants', [])
            
            product, created = Product.objects.update_or_create(
                slug=p_info['slug'],
                defaults=p_info
            )
            
            # Seed Images
            for idx, img_info in enumerate(images):
                img_info['sort_order'] = idx
                ProductImage.objects.update_or_create(
                    product=product,
                    image=img_info['image'],
                    defaults=img_info
                )
                
            # Seed Variants
            for v_info in variants:
                ProductVariant.objects.update_or_create(
                    product=product,
                    sku=v_info['sku'],
                    defaults=v_info
                )
                
            # Sample Reviews for the product
            if product.slug == 'royal-blue-lotus-24k-gold-serum':
                reviews_seed = [
                    {
                        'author_name': 'فريدة الشافعي',
                        'governorate': 'القاهرة (الزمالك)',
                        'rating': 5,
                        'title': 'إكسير سحري خفف التصبغات في 10 أيام فقط!',
                        'comment': 'سيروم فاخر بكل معنى الكلمة، ملمسه مائي خفيف يمتص بثوانٍ في رطوبة الصيف بالقاهرة ورائحته كأنكِ تمشين في حديقة لوتس نيلية. رقائق الذهب تذوب وتترك بريقاً طبيعياً رائعاً بدون أي لمعان دهني.',
                        'is_verified_purchase': True,
                    },
                    {
                        'author_name': 'ياسمين قنديل',
                        'governorate': 'الإسكندرية (سموحة)',
                        'rating': 5,
                        'title': 'أفضل منتج عناية مصري جربته بحياتي',
                        'comment': 'التغليف الملكي فاق توقعاتي والصندوق الخشبي بالشمع رائع كهدية. الشحن وصلني بالإسكندرية خلال 48 ساعة والدفع عند الاستلام بعد المعاينة أعطاني طمأنينة تامة.',
                        'is_verified_purchase': True,
                    },
                    {
                        'author_name': 'مريم عبد العزيز',
                        'governorate': 'الجيزة (الشيخ زايد)',
                        'rating': 5,
                        'title': 'ترطيب عميق وحماية من شمس زايد',
                        'comment': 'بشرتي حساسة جداً وجافة، هذا السيروم مع كريم الهيالورونيك هو روتيني اليومي الآن. مسجل بوزارة الصحة ونتائجه واضحة من أول أسبوع.',
                        'is_verified_purchase': True,
                    },
                ]
                for r_data in reviews_seed:
                    ProductReview.objects.get_or_create(
                        product=product,
                        author_name=r_data['author_name'],
                        defaults=r_data
                    )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(products_data)} luxury products with variants, images & verified reviews.'))
        self.stdout.write(self.style.SUCCESS('LUMÉ database seeding completed flawlessly!'))
