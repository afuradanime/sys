# Administração de sistemas e deployment
Este repositório consiste em scripts, _tools_ de manutenção, documentação global sobre o quesito físico, monitorização de processos e eventuais automatizações.

## Como formar a base de dados de animes
A base de dados consiste inteiramente de informação open source. Para criar a base de dados existem alguns scripts python e um _Makefile_ na pasta `/scripts`. A informação da base de dados é proveniente do site [MyAnimeList](https://myanimelist.net/), extraída pelo _API_ não oficial [Jikan](https://jikan.moe/).

A formação da base de dados consiste de dois passos:
1. A extração da informação.
2. O _bootstrapping_ e inserção da informação num ficheiro SQLite.

No ficheiro `/scripts/Makefile` podem ser mudadas as constantes de nomes de ficheiros caso tal seja desejado. O target `make all` irá executar todos os scripts e automaticamente resultar numa base de dados formada no caminho indicado. Esta base de dados está agora pronta para ser usada pelo API.

> [!WARNING]  
> Este processo pode demorar mais de 10 minutos.