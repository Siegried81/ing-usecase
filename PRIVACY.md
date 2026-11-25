# Privacy notice

This is a student project built for an ING use case. It compares the public
marketing pages of Belgian banks. It has no user accounts and asks no one for
personal data.

## Who is responsible

The project's authors. Contact them by opening an issue on
[the repository](https://github.com/Siegried81/ing-usecase/issues).

## What it collects

**About banks.** Screenshots and text of public marketing pages, fetched only
where the bank's `robots.txt` allows it. No login, no customer area. These pages
can show people (models in campaign photos, a quoted spokesperson). That's the
only personal data the pipeline sees, and it isn't extracted or stored as such:
the features are about the campaign (colours, wording, offer), never about a
person.

**About news.** When a NewsAPI key is set, recent headlines that mention each
bank. Headlines can name public figures. They're kept as theme counts plus up to
5 headlines per bank, with their source link.

**About you, if you use the dashboard or the web UI.**

- The host keeps standard access logs: IP address, time, page requested. We
  don't read them for anything other than fixing errors, and we don't copy them
  anywhere.
- Streamlit's usage statistics are switched off (`.streamlit/config.toml`).
- The only cookie is the one Streamlit needs for its own request protection.
- If the API asks for an access token, your browser keeps it in
  `sessionStorage`. It's gone when you close the tab.
- A search on the Research tab sends your query to Semantic Scholar.

## Why, and on what basis

The page captures and headlines are there to compare how banks communicate.
The access logs are there to keep the site running and fix errors. Both rest on
legitimate interest (GDPR Art. 6(1)(f)). Nothing here relies on your consent, so
there's no consent to withdraw.

## Outside services

Data leaves the machine running the code only through these services, and only
when their key is set in `.env`.

| Service | What it receives | Company based in |
| --- | --- | --- |
| DeepSeek (pinned model) | page text, analysis summary, headlines | China |
| Groq (fallback) | same | United States |
| OpenRouter (fallback) | same, passed on to the model's own host | United States |
| Cerebras (fallback) | same | United States |
| SambaNova (fallback) | same | United States |
| Ollama (fallback) | same, but runs locally: nothing leaves the machine | local |
| NewsAPI.org, newsapi.ai | the bank name as a search term | see their terms |
| Semantic Scholar | your Research query | United States |
| Finnhub | a stock ticker | United States |
| Render (hosting) | the access logs above | servers in Frankfurt |

The models get page text, never anything typed by a visitor. DeepSeek is the
pinned model. The others are fallbacks, tried in the order above only when the
one before fails, and the model that answered is recorded per row in
`extraction_model`.

Sending text to a provider outside the EU is a transfer under GDPR Art. 44. What
goes out today is public page text and public headlines. Before any real use
with ING data, each provider's location and transfer terms (standard contractual
clauses, data retention, training on inputs) have to be checked against its
current contract. That check hasn't been done.

## Your rights

You can ask to see what we hold about you, have it corrected or deleted, limit
how it's used, get a copy, or object to its use. Open an issue on the
repository. We hold nothing about visitors beyond the host's logs.

If you think your data was handled wrongly, please open an issue first. You can
also complain to the Belgian Data Protection Authority (APD/GBA,
[dataprotectionauthority.be](https://www.dataprotectionauthority.be)).
