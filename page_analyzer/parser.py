from bs4 import BeautifulSoup


def get_seo_info(web_page):
    soup = BeautifulSoup(web_page.text, 'html.parser')
    site_data = {}

    if soup.h1:
        site_data['h1'] = soup.h1.text
    else:
        site_data['h1'] = ''

    if soup.title:
        site_data['title'] = soup.title.text
    else:
        site_data['title'] = ''

    if soup.find('meta', attrs={'name': 'description'}):
        site_data['description'] = (
            soup.find('meta', attrs={'name': 'description'}).get('content'))
    else:
        site_data['description'] = ''

    return site_data
