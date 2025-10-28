from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Input, Button
from textual.reactive import reactive
from textual.containers import Center, Container
from textual.screen import Screen
from textual import on
from ics import Calendar, Event
from datetime import datetime, date
import re, requests, os, webbrowser, json, sys, platform, subprocess

# Get base path for PyInstaller bundled files
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Get the program data directory for each platform
def getDataDir():
    if platform.system() == 'Windows': # Windows
        base = os.getenv('LOCALAPPDATA')
    elif platform.system() == 'Darwin': # macOS
        base = os.path.expanduser('~/Library/Application Support')
    else: # Linux and others
        base = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    
    return os.path.join(base, 'ingStudios', 'Vyntr for Desktop')

searchHistory = []
vyntrApiKey = ''

class WebResult(Container):
    def __init__(self, title: str, url: str, preview: str, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self.url = url
        self.can_focus = True
        self.title_text = title
        self.url_text = url
        self.preview_text = preview
    
    def compose(self) -> ComposeResult:
        yield Static(self.title_text, classes="result_title")
        yield Static(self.url_text, classes="result_url")
        yield Static(self.preview_text, classes="result_preview")
    
    def on_click(self) -> None:
        webbrowser.open(self.url)

class BliptextContainer(Container):
    def __init__(self, title: str, summary:str, slug: str, keys: list, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self.title = title
        self.summary = summary
        self.slug = slug
        self.url = f'https://bliptext.com/articles/{slug}'
        self.keys = keys
        self.can_focus = True

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="bliptext_title")
        yield Static(self.url, classes="bliptext_url")
        for key in self.keys:
            yield Static(f"{key.get('key')}: {key.get('value')}", classes="bliptext_property")
        yield Static(self.summary, classes="bliptext_intro")

    def on_click(self) -> None:
        webbrowser.open(self.url)

class DateContainer(Container):
    def __init__(self, description: str, date: datetime, displayText: str, **kwargs):
        super().__init__(**kwargs)
        self.description = description
        self.can_focus = True
        
        # Handle ISO 8601 date parsing
        if isinstance(date, str):
            try:
                date_str = date.replace('Z', '+00:00')
                self.date = datetime.fromisoformat(date_str)
            except:
                try:
                    # Fallback: try other common formats
                    self.date = datetime.strptime(date, "%Y-%m-%d")
                except:
                    self.date = datetime.now()
        elif isinstance(date, datetime):
            self.date = date
        else:
            self.date = datetime.now()
            
        self.date_str = self.date.strftime("%d/%m/%Y")
        self.displayText = displayText
    
    def compose(self) -> ComposeResult:
        yield Static(self.description, classes="date_description")
        yield Static(self.displayText, classes="date_display")
        yield Static(self.date_str, classes="date_date")

    def on_click(self) -> None:
        try:
            c = Calendar()
            e = Event()
            e.name = self.description
            e.begin = self.date
            e.description = f'{self.description} - Exported by Vyntr for Desktop'
            c.events.add(e)

            # Sanitize filename - remove invalid characters
            safe_filename = "".join(c for c in self.description if c.isalnum() or c in (' ', '-', '_')).rstrip()
            pathToSave = os.path.join(getDataDir(), f'{safe_filename}_event.ics')
            os.makedirs(os.path.dirname(pathToSave), exist_ok=True)

            with open(pathToSave, 'w') as f:
                f.writelines(c.serialize_iter())

            if platform.system() == 'Windows': # Windows
                os.startfile(pathToSave)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(['open', pathToSave]);
            else: # Linux and others
                subprocess.call(['xdg-open', pathToSave])
        except Exception as e:
            print(f"An error occurred: {e}")


class WordContainer(Container):
    def __init__(self, word: str, partOfSpeech: str, definitions: list, synonyms: list, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
        self.word = word
        self.partOfSpeech = partOfSpeech
        self.definitions = definitions
        self.synonyms = synonyms

    def compose(self) -> ComposeResult:
        yield Static(self.word, classes="word_word")
        yield Static(self.partOfSpeech, classes="word_pos")

        yield Container(
            *[
                Static(f'{index + 1}. {definition.get("gloss")} ({definition.get("pos")})', classes="definition")
                for index, definition in enumerate(self.definitions)
            ],
            classes="definitions_container"
        )

        if (self.synonyms is not None):
            yield Static('Similar:', classes="synonyms_header")
            yield Container(
                *[
                    Static(synonym, classes="synonym")
                    for synonym in self.synonyms
                ],
                classes="synonyms_container"
            )

class CurrencyContainer(Container):
    def __init__(self, baseCurrency: dict, convertedCurrency: dict, rate: int, lastUpdated: datetime, **kwargs):
        super().__init__(**kwargs)
        self.baseCurrency = baseCurrency
        self.convertedCurrency = convertedCurrency
        self.rate = rate

        # Handle ISO 8601 date parsing
        if isinstance(lastUpdated, str):
            try:
                date_str = lastUpdated.replace('Z', '+00:00')
                self.lastUpdated = datetime.fromisoformat(date_str)
            except:
                try:
                    # Fallback: try other common formats
                    self.lastUpdated = datetime.strptime(lastUpdated, "%Y-%m-%d")
                except:
                    self.lastUpdated = datetime.now()
        elif isinstance(lastUpdated, datetime):
            self.lastUpdated = lastUpdated
        else:
            self.lastUpdated = datetime.now()

    def compose(self) -> ComposeResult:
        yield Static(f"{round(self.baseCurrency.get('amount'), 2)} {self.baseCurrency.get('code')} ≈", classes="base_currency")
        yield Static(f"{round(self.convertedCurrency.get('amount'), 2)} {self.convertedCurrency.get('code')}", classes="converted_currency")
        yield Static(f"1 {self.baseCurrency.get('code')} ≈ {round(self.rate, 2)} {self.convertedCurrency.get('code')}", classes="exchange_rate")
        yield Static(f"Last updated on {self.lastUpdated.strftime('%B %d, %Y at %I:%M %p')}", classes="currency_last_updated")

    def on_click(self) -> None:
        webbrowser.open('https://github.com/fawazahmed0/exchange-api')

class UnitConversionContainer(Container):
    def __init__(self, value: int, fromUnit: str, toUnit: str, category: str, result: int, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.fromUnit = fromUnit
        self.toUnit = toUnit
        self.category = category
        self.result = result

    def compose(self) -> ComposeResult:
        yield Static(f'{str(round(self.value, 2))} {self.fromUnit} ≈', classes="initial_value")
        yield Static(f'{str(round(self.result,2))} {self.toUnit}', classes="converted_value")
        yield Static(f'Converting {self.category}', classes="conversion_category")

class SetApiKeyButton(Button):
    def __init__(self, **kwargs):
        super().__init__(label="Set API key", **kwargs)

class VyntrForDesktop(App):
    CSS_PATH = os.path.join(base_path, "style.tcss")

    BINDINGS = [
        ("q", "quit", "Quit App"),
        ("h", "displaySearchHistory", "Search History"),
    ]

    TITLE = 'Vyntr for Desktop'

    pathToSave = os.path.join(getDataDir(), 'program_data.json')
    
    os.makedirs(os.path.dirname(pathToSave), exist_ok=True)
    
    if not os.path.exists(pathToSave):
        with open(pathToSave, 'w') as f:
            json.dump({}, f)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static('Vyntr for Desktop', classes="vyntr_title")
        yield Static('Welcome to Vyntr for Desktop! Enter your API key (https://vyntr.com/api) and start searching to get started!', classes="welcome_text")
        with Center():
            yield Input(placeholder="How do I cook...", id="search_input")
            yield Input(placeholder="Vyntr API key", id="api_input", classes="hidden", value=vyntrApiKey)
        with Center():
            yield SetApiKeyButton(id="show_api")
        with Center():
            yield Container(id="search_results_container")
        yield Footer()

    def on_mount(self) -> None:
        self.loadProgramData()

    def displaySearchResults(self, searchResults, searchQuery):
        searchResultsContainer = self.query_one("#search_results_container")
        searchResultsContainer.remove_children()

        webResults = searchResults.get('web', [])
        bliptextCard = searchResults.get('bliptext')
        dateCard = searchResults.get('date')
        wordCard = searchResults.get('word')
        currencyCard = searchResults.get('currency')
        unitConversionCard = searchResults.get('unitConversion')
        aiSummary = searchResults.get('ai_summary')

        # Display date card
        if dateCard is not None:
            dateContainer = DateContainer(
                dateCard.get('description', 'Date'),
                dateCard.get('date'),
                dateCard.get('displayText', ''),
                classes="date_card"
            )
            searchResultsContainer.mount(Center(dateContainer))

        # Display currency card
        if currencyCard is not None:
            currencyContainer = CurrencyContainer(
                currencyCard.get('from'),
                currencyCard.get('to'),
                currencyCard.get('rate'),
                currencyCard.get('lastUpdated'),
                classes="currency_card"
            )
            searchResultsContainer.mount(Center(currencyContainer))

        # Display word card
        if wordCard is not None:
            wordContainer = WordContainer(
                wordCard.get('word'),
                wordCard.get('partOfSpeech'),
                wordCard.get('definitions'),
                wordCard.get('synonyms'),
                classes="word_card"
            )
            searchResultsContainer.mount(Center(wordContainer))

        # Display unit conversion card
        if unitConversionCard is not None:
            unitConversionContainer = UnitConversionContainer(
                unitConversionCard.get('value'),
                unitConversionCard.get('fromUnit'),
                unitConversionCard.get('toUnit'),
                unitConversionCard.get('category'),
                unitConversionCard.get('result'),
                classes="unit_conversion_card"
            )
            searchResultsContainer.mount(Center(unitConversionContainer))

        # Display Bliptext card
        if bliptextCard is not None:
            article = bliptextCard.get('article', {})
            summary = article.get('summary', {})
            
            bliptextContainer = BliptextContainer(
                article.get('title', 'No title'),
                summary.get('introduction', 'No summary'),
                article.get('slug', ''),
                summary.get('keys', []),
                classes="bliptext_card"
            )
            searchResultsContainer.mount(Center(bliptextContainer))

        # Display web results
        if webResults:
            for index, result in enumerate(webResults):
                self.log(f'Result {index + 1} of {len(webResults)}:', result.get('title'))

                resultContainer = WebResult(
                    result.get('title', 'No title'),
                    result.get('url', ''),
                    result.get('preview') or 'No information is available.',
                    classes="search_result_item"
                )
                searchResultsContainer.mount(Center(resultContainer))
        else:
            if all(card is None for card in [bliptextCard, dateCard, wordCard, currencyCard, unitConversionCard]):
                searchResultsContainer.mount(
                    Center(Static(f"No search results found for '{searchQuery}'.", classes="no_results"))
                )

    @on(Input.Submitted, '#search_input')
    async def fetchSearchResults(self, event: Input.Submitted) -> None:
        searchQuery = event.value
        self.log('Searched:', searchQuery)

        searchQueryToFetch = re.sub(r" ", "%20", searchQuery, flags=re.IGNORECASE)

        headers = {
            'Authorization': f'Bearer {vyntrApiKey}'
        }

        BASE_URL = f'https://vyntr.com/api/v1/search?q={searchQueryToFetch}'
        self.log('Fetching:', BASE_URL)

        searchResultsContainer = self.query_one("#search_results_container")

        try:
            response = requests.get(BASE_URL, headers=headers)
            self.log('Status code:', response.status_code)
            self.log(response.json())

            if response.status_code == 200:
                self.log('Fetch result successful.')
                searchHistory.insert(0, { 'query': searchQuery, 'date': date.today().strftime("%d %m %Y") })
                self.displaySearchResults(response.json(), searchQuery)
            elif response.status_code == 401:
                self.log('API key invalid or missing.')
                searchResultsContainer.remove_children()
                searchResultsContainer.mount(
                    Center(Static('Please enter a valid Vyntr API key.', classes="error_text"))
                )
            elif response.status_code == 429:
                self.log('API requests rate limit exceeded')
                searchResultsContainer.remove_children()
                searchResultsContainer.mount(
                    Center(Static('Your Vyntr API rate limit has exceeded. Please try again later or purchase more credits at https://vyntr.com/api.', classes="error_text"))
                )
            elif response.status_code == 500:
                self.log('An internal server error on Vyntr API occurred')
                searchResultsContainer.remove_children()
                searchResultsContainer.mount(
                    Center(Static('An unexpected error occurred, please try again later.', classes="error_text"))
                )
        except requests.exceptions.RequestException as e:
            self.log('An unexpected error occurred during fetch:', e)
            searchResultsContainer.remove_children()
            searchResultsContainer.mount(
                Center(Static('An unexpected error occurred while fetching search results. Please ensure you are connected to the internet and try again.', classes="error_text"))
            )

    def saveProgramData(self):
        global vyntrApiKey
        apiKey = self.query_one("#api_input", Input).value
        
        fileContent = {
            'apiKey': apiKey,
            'history': searchHistory
        }

        vyntrApiKey = apiKey

        with open(self.pathToSave, 'w') as file:
            json.dump(fileContent, file)

    def loadProgramData(self):
        global vyntrApiKey, searchHistory
        try:
            if os.path.exists(self.pathToSave):
                with open(self.pathToSave, 'r') as file:
                    content = file.read().strip()
                    if content:
                        data = json.loads(content)

                        # Assign each property to its variables
                        vyntrApiKey = data.get('apiKey', '')
                        searchHistory = data.get('history', [])

                        # Set the API key input value to the loaded API key
                        api_input_widget = self.query_one("#api_input", Input)
                        api_input_widget.value = vyntrApiKey
        except json.JSONDecodeError:
            self.log("Error loading program data: Invalid JSON")
        except Exception as e:
            self.log(f"Error loading program data: {e}")

    @on(Input.Submitted, '#api_input')
    def saveApiKey(self, event: Input.Submitted) -> None:
        self.saveProgramData()
        self.notify('Vyntr API key saved successfully.', timeout=1.5)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        buttonId = event.button.id

        if buttonId == "show_api":
            self.query_one("#api_input").toggle_class("hidden")

    def action_quit(self) -> None:
        self.saveProgramData()
        self.exit()

    def action_displaySearchHistory(self) -> None:
        self.push_screen(SearchHistoryScreen())

class SearchHistoryItem(Container):
    def __init__(self, itemSearched: str, dateSearched: str, index: int, **kwargs):
        super().__init__(**kwargs)
        self.itemSearched = itemSearched
        self.dateSearched = dateSearched
        self.index = index

    def compose(self) -> ComposeResult:
        if self.dateSearched:
            yield Static(self.dateSearched, classes="date_searched")
        else:
            yield Static('Unknown date', classes="date_searched")

        yield Static(self.itemSearched, classes="item_searched")
        yield Button("Delete", id=f"delete_{self.index}", classes="delete_history_button")

class SearchHistoryScreen(Screen):
    CSS_PATH = os.path.join(base_path, "style.tcss")

    BINDINGS = [
        ("escape", "app.pop_screen", "Back")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static('Search History', classes="search_history_title")
        for index, searchedItem in enumerate(searchHistory):
            searchedQuery = searchedItem.get('query', 'Unknown query')
            searchedDate = searchedItem.get('date', 'Unknown date')
            yield Center(
                SearchHistoryItem(searchedQuery, searchedDate, index, classes="search_history_item")
            )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("delete_"):
            # Extract the index from the button ID
            index = int(event.button.id.split("_")[1])
            
            # Remove from global searchHistory
            global searchHistory
            if 0 <= index < len(searchHistory):
                del searchHistory[index]
                
                # Save the updated history
                self.app.saveProgramData()
                
                # Refresh the screen
                self.refresh(recompose=True)
                self.app.notify('Search history item deleted.', timeout=1.5)

if __name__ == "__main__":
    app = VyntrForDesktop()
    app.run()