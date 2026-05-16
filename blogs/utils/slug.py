from django.utils.text import slugify


def get_slug(text, obj,  pk):
    base_slug = slugify(text, allow_unicode=True)
    slug = base_slug
    counter = 1

    klass = obj.__class__
    while klass.objects.filter(slug=slug).exclude(pk=pk).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
