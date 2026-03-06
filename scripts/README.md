## Mudanças ao `import_to_sqlite.py`/`scraper.py` - 2026/03
1. Removido o "type" das tabelas de produtor e licenciador por serem irrelevantes
2. Removido "language" da tabela de descriptions, isso está a ser guardado no mongo e viola a idea de que eta DB é readonly
3. Removida tabela language
4. Adicionada informação extra sobre estúdios, productores e licenciadores, também adicionada informação de relação de animes. Tempo de execução do scraper.py altamente aumentado. 

Mudança de planos, estava a demorar wayyyy too much. Vou fazer uma flag para escolher ir buscar cada tipo de informação uma de cada vez e esperançosamente fica tudo +/- igual