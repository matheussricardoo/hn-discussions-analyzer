import requests
from operator import itemgetter
import pygal
from pygal.style import LightColorizedStyle as LCS, LightenStyle as LS
from requests.exceptions import RequestException

# Configurações
URL_TOP_STORIES = 'https://hacker-news.firebaseio.com/v0/topstories.json'
URL_SUBMISSION = 'https://hacker-news.firebaseio.com/v0/item/{}.json'
MAX_STORIES = 30
MAX_RETRIES = 3
OUTPUT_FILENAME = 'hn_discussions.svg'
HEADERS = {'User-Agent': 'Python/HackerNews Top Stories Analyzer'}

def fetch_top_stories():
    """Obtém os IDs das histórias mais populares do Hacker News."""
    try:
        response = requests.get(URL_TOP_STORIES, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f'Erro ao buscar top stories: {e}')
        return None

def fetch_story_details(story_id, retries=MAX_RETRIES):
    """Busca detalhes de uma história com tratamento de erros e retentativas."""
    for attempt in range(retries):
        try:
            url = URL_SUBMISSION.format(story_id)
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt < retries - 1:
                print(f'Retentativa {attempt + 1} para story ID {story_id}')
                continue
            print(f'Falha ao buscar story ID {story_id}: {e}')
            return None

def process_stories(story_ids):
    """Processa as histórias e retorna os dados formatados."""
    stories = []
    for story_id in story_ids[:MAX_STORIES]:
        data = fetch_story_details(story_id)
        if data:
            story = {
                'title': data.get('title', 'Título não disponível'),
                'comments': data.get('descendants', 0),
                'link': f'http://news.ycombinator.com/item?id={story_id}',
                'score': data.get('score', 0)  # Adicionado como critério de desempate
            }
            stories.append(story)
    return sorted(stories, key=itemgetter('comments', 'score'), reverse=True)

def generate_chart(stories):
    """Gera um gráfico SVG com os dados processados."""
    # Preparar dados para visualização
    plot_data = [{
        'value': story['comments'],
        'label': f"{story['title']} ({story['comments']} comentários)",
        'xlink': story['link']
    } for story in stories]

    # Configurar estilo do gráfico
    style = LS('#336699', base_style=LCS)
    style.title_font_size = 24
    style.label_font_size = 12
    style.major_label_font_size = 14

    # Criar e configurar gráfico
    chart = pygal.HorizontalBar(
        style=style,
        show_legend=False,
        truncate_label=15,
        tooltip_border_radius=10,
        width=1200,
        height=800
    )
    
    chart.title = 'Hacker News: Discussões Mais Populares (Top 30)'
    chart.x_title = 'Número de Comentários'
    
    # Adicionar dados ao gráfico
    chart.add('', plot_data)
    
    # Salvar o gráfico
    chart.render_to_file(OUTPUT_FILENAME)
    print(f'Gráfico salvo como {OUTPUT_FILENAME}')

def main():
    """Fluxo principal da aplicação."""
    story_ids = fetch_top_stories()
    if not story_ids:
        return

    processed_stories = process_stories(story_ids)
    if not processed_stories:
        print('Nenhuma história válida encontrada.')
        return

    generate_chart(processed_stories)

if __name__ == '__main__':
    main()
