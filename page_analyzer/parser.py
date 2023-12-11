from bs4 import BeautifulSoup


def get_seo_info(web_page):
    soup = BeautifulSoup(web_page.text, 'html.parser')
    site_data = dict()

    site_data['h1'] = soup.h1.text if soup.h1 else ''
    site_data['title'] = soup.title.text if soup.title else ''
    if soup.find('meta', attrs={'name': 'description'}):
        site_data['description'] = (
            soup.find('meta', attrs={'name': 'description'}).get('content'))
    else:
        site_data['description'] = ''

    return site_data
