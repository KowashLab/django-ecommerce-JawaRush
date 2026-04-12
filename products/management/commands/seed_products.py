import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from products.models import Category, Product

CATEGORIES = [
    {'name': 'Hops', 'slug': 'hops'},
    {'name': 'Malts', 'slug': 'malts'},
    {'name': 'Yeast', 'slug': 'yeast'},
    {'name': 'Kits', 'slug': 'kits'},
]

PRODUCTS = [
    {
        'name': 'Caramel Malt 60L',
        'slug': 'caramel-malt',
        'price': '3.00',
        'image': 'caramel_malt.jpg',
        'category': 'malts',
        'stock': 50,
        'description': (
            'Caramel Malt 60L (also known as Crystal 60L) is a versatile specialty malt '
            'that is a secret weapon for many brewers to enhance beer color, flavor, and body. '
            'It imparts a beautiful copper-amber hue to the brew.\n\n'
            'The flavor of this malt is characterized by distinct notes of caramel, toffee, '
            'and light hints of toasted bread. It adds a pleasant sweetness to the beer that '
            'beautifully balances hop bitterness and also contributes to improved head retention.\n\n'
            'Caramel Malt 60L is ideal for a wide range of styles, from Pale Ales and Amber Ales '
            'to Porters and Stouts, adding complexity and depth.'
        ),
    },
    {
        'name': 'Cascade Hops',
        'slug': 'cascade-hops',
        'price': '7.49',
        'image': 'cascade_hops.jpg',
        'category': 'hops',
        'stock': 40,
        'description': (
            'Cascade is arguably the most famous hop in the American craft brewing revolution. '
            'Developed in Oregon, it has a unique floral and citrus character that defined the '
            'taste of the classic American Pale Ale.\n\n'
            'Its moderate bitterness and vibrant aroma, with notes of grapefruit, orange, and '
            'light floral undertones, make it incredibly versatile. Cascade is excellent for '
            'both bittering and late kettle additions or for dry hopping.\n\n'
            'This hop is a reliable choice for brewers looking to create a refreshing, balanced, '
            'and recognizable ale.'
        ),
    },
    {
        'name': 'Centennial Hops',
        'slug': 'centennial-hops',
        'price': '6.20',
        'image': 'centennial_hops.jpg',
        'category': 'hops',
        'stock': 35,
        'description': (
            'Centennial is a classic American hop often referred to as "Super Cascade" due to '
            'its similar citrus profile but with a higher intensity and alpha acid content. '
            'It is one of the "Three Cs" (along with Cascade and Columbus) that defined the '
            'flavor of American IPAs.\n\n'
            'The aroma of Centennial is powerful, with bright notes of lemon, grapefruit, and '
            'pronounced floral undertones. Thanks to its high alpha acid content, it is excellent '
            'for both bittering and creating an intense aroma.\n\n'
            'This is an extremely versatile hop, perfect for American Pale Ales, IPAs, and '
            'Double IPAs, giving them a bright and recognizable character.'
        ),
    },
    {
        'name': 'Citra Hops',
        'slug': 'citra-hops',
        'price': '5.99',
        'image': 'citra_hops.jpg',
        'category': 'hops',
        'stock': 30,
        'description': (
            'Citra is one of the most sought-after and recognizable hop varieties in the world '
            'of craft brewing, famous for its bright and multifaceted citrus aroma. Developed '
            'in the USA, this variety is ideal for IPAs, Pale Ales, and other styles where a '
            'distinct fruity profile is desired.\n\n'
            'Citra boasts a high alpha acid content, making it excellent for both bitterness '
            'and intense aroma. It imparts notes of grapefruit, lime, passion fruit, lychee, '
            'and melon to beer, creating a unique tropical bouquet.\n\n'
            'Our T-90 pellets are hermetically sealed to preserve freshness and maximum aromatics.'
        ),
    },
    {
        'name': 'Imperial Organic Yeast A07',
        'slug': 'imperial-yeast',
        'price': '8.99',
        'image': 'imperial_yeast.jpg',
        'category': 'yeast',
        'stock': 25,
        'description': (
            'Imperial Organic Yeast A07 "Flagship" is a versatile and extremely popular liquid '
            'yeast, known for its ability to create balanced ales with a light fruity character. '
            'This strain is a true workhorse and is perfect for most American beer styles.\n\n'
            '"Flagship" provides a clean fermentation with light ester notes of citrus and stone '
            'fruit that complement, rather than overpower, the hop and malt profile. It has good '
            'attenuation and moderate flocculation, leaving behind a soft and smooth mouthfeel.\n\n'
            'Thanks to the high cell count per package (200 billion), this yeast does not require '
            'a starter for most standard batches of beer, making it a convenient and reliable choice.'
        ),
    },
    {
        'name': 'Maris Otter Pale Malt',
        'slug': 'maris-otter-malt',
        'price': '2.50',
        'image': 'maris_otter_malt.jpg',
        'category': 'malts',
        'stock': 60,
        'description': (
            'Maris Otter Pale Malt is the cornerstone of British brewing heritage, a revered '
            'base malt prized by brewers worldwide for its exceptional quality and flavor.\n\n'
            'It provides a rich, slightly sweet, and biscuity malt backbone that is more complex '
            'than standard 2-row malts, with subtle nutty undertones that enhance any beer style. '
            'Perfect for creating authentic British ales such as Bitters, IPAs, Porters, and Stouts.\n\n'
            'Its excellent processing characteristics and high extract yield make it a reliable '
            'and efficient choice for both novice and experienced brewers.'
        ),
    },
    {
        'name': 'Mosaic Hops',
        'slug': 'mosaic-hops',
        'price': '9.50',
        'image': 'mosaic_hops.jpg',
        'category': 'hops',
        'stock': 20,
        'description': (
            'Mosaic is one of the most vibrant and multifaceted hops on the modern craft scene. '
            'As a "daughter" of Simcoe, it inherited the best from its lineage and added a unique '
            'palette of aromas, making it a true aromatic bomb.\n\n'
            'The name "Mosaic" is fully justified: it creates a complex mosaic of flavors and '
            'aromas, including notes of tropical fruits (mango, guava), citrus (tangerine), '
            'berries (blueberry), stone fruits (peach), and even light pine and earthy undertones.\n\n'
            'This hop is ideal for dry hopping in IPA and Pale Ale styles, where it can unleash '
            'its full potential, creating a juicy, vibrant, and unforgettable beer.'
        ),
    },
    {
        'name': 'Pilsner Malt',
        'slug': 'pilsner-malt',
        'price': '2.20',
        'image': 'pilsner_malt.jpg',
        'category': 'malts',
        'stock': 70,
        'description': (
            'Pilsner Malt is the lightest base malt, forming the foundation for classic German '
            'and Czech pilsners, as well as a multitude of other light lagers and ales. It is '
            'produced from high-quality two-row barley and undergoes gentle kilning at low temperatures.\n\n'
            'This malt imparts a very light, straw-like color and a clean, slightly sweet, grainy '
            'flavor to the beer. Its neutral character allows the aroma of hops and the work of '
            'the yeast to fully express themselves, making it an ideal base for beers where purity '
            'and crispness are paramount.\n\n'
            'Thanks to its high enzymatic activity, Pilsner Malt is excellent for mashes with a '
            'large proportion of unmalted grains.'
        ),
    },
    {
        'name': 'Saaz Hops',
        'slug': 'saaz-hops',
        'price': '4.75',
        'image': 'saaz_hops.jpg',
        'category': 'hops',
        'stock': 45,
        'description': (
            'Saaz is a noble hop, the heart and soul of classic Bohemian and Czech pilsners. '
            'Grown in the Zatec region of the Czech Republic, it possesses a delicate and refined '
            'aromatic profile that is unmistakable.\n\n'
            'Its aroma is characterized by soft, spicy, herbal, and floral notes. Saaz is primarily '
            'used for aroma rather than bitterness, as its alpha acid content is low. It imparts a '
            'classic European elegance and clean taste to the beer.\n\n'
            'If you aim to brew an authentic Czech pilsner, European lager, or Belgian ale, Saaz '
            'is an indispensable ingredient.'
        ),
    },
    {
        'name': 'SafAle US-05 Dry Ale Yeast',
        'slug': 'safale-us05-yeast',
        'price': '3.25',
        'image': 'safale_us05_yeast.jpg',
        'category': 'yeast',
        'stock': 55,
        'description': (
            'SafAle US-05 is the most famous and popular American ale yeast in the world. This '
            'strain is renowned for its ability to produce clean, crisp beers with a neutral flavor '
            'profile, allowing the hop and malt character to shine through.\n\n'
            'With its high attenuation and high flocculation, US-05 is ideal for a wide range of '
            'American ale styles, from West Coast IPAs to American Pale Ales and Cream Ales. It '
            'forms a firm sediment, making racking and clarification easier.\n\n'
            'Reliable, easy to use, and available in a dry format, this yeast is the number one '
            'choice for brewers seeking consistent and predictable results.'
        ),
    },
    {
        'name': 'Unmalted Wheat',
        'slug': 'unmalted-wheat',
        'price': '1.80',
        'image': 'unmalted_wheat.jpg',
        'category': 'malts',
        'stock': 80,
        'description': (
            'Unmalted wheat is the secret ingredient behind the classic hazy, refreshing character '
            'of Belgian Witbier. Unlike malted wheat, this is raw, unprocessed grain that imparts '
            'a unique texture and flavor to the beer.\n\n'
            'Using unmalted wheat provides the beer with its characteristic light haze, a smooth, '
            'silky body, and a subtle, bready-grainy flavor that doesn\'t overpower the delicate '
            'notes of coriander and orange peel. The high protein content of this grain also '
            'contributes to a dense and persistent head.\n\n'
            'This ingredient is a must-have for any brewer aiming to recreate an authentic Belgian '
            'Witbier or to add complexity and body to other styles, such as Lambics.'
        ),
    },
    {
        'name': 'West Coast IPA - All-Grain Kit',
        'slug': 'west-coast-ipa-kit',
        'price': '60.00',
        'image': 'ipa_kit.jpg',
        'category': 'kits',
        'stock': 15,
        'description': (
            'Brew a craft brewing classic with our "West Coast IPA - All-Grain Kit"! This kit '
            'contains all the necessary ingredients to create a bright, bitter, and incredibly '
            'aromatic IPA in the style of the US West Coast.\n\n'
            'We\'ve selected the perfect combination of malts to achieve a clean, dry body that '
            'serves as an excellent base for a hop explosion. The kit includes a powerful combination '
            'of Centennial, Simcoe, and Columbus hops, which provide a burst of citrus, pine, and '
            'resinous notes characteristic of this style.\n\n'
            'This kit is your ticket to the world of true West Coast IPA. It comes with detailed '
            'step-by-step instructions to guide you through every stage, from mashing to bottling.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Seed the database with categories and products'

    def handle(self, *args, **options):
        # Create categories
        categories = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name']},
            )
            categories[cat.slug] = cat
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Category "{cat.name}" — {status}')

        # Copy static images to media/products/
        static_products_dir = settings.BASE_DIR / 'static' / 'img' / 'products'
        media_products_dir = settings.MEDIA_ROOT / 'products'
        media_products_dir.mkdir(parents=True, exist_ok=True)

        for img_file in static_products_dir.iterdir():
            dest = media_products_dir / img_file.name
            if not dest.exists():
                shutil.copy2(img_file, dest)

        # Create products
        for p in PRODUCTS:
            product, created = Product.objects.get_or_create(
                slug=p['slug'],
                defaults={
                    'name': p['name'],
                    'price': p['price'],
                    'description': p['description'],
                    'category': categories[p['category']],
                    'image': f"products/{p['image']}",
                    'stock': p['stock'],
                    'is_active': True,
                },
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Product "{product.name}" — {status}')

        self.stdout.write(self.style.SUCCESS(
            f'Done: {Product.objects.count()} products, '
            f'{Category.objects.count()} categories'
        ))
