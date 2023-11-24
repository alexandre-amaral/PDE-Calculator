# PDE Calculator

## Contributing
### Arquitetura

1. `Extractor` recebe o nome do composto e extrai os dados da API;
2. `TextMining` extrai as informações relevantes do que foi recebido e gera um `Assay`;
3. `PDE` recebe um objeto `Assay`, que contém todas as informações relevantes;
### Configuração do ambiente
Para configurar seu ambiente para executar o projeto, é importante que você instale:
- [git](https://git-scm.com/)
- [miniconda](https://docs.conda.io/en/latest/miniconda.html) (ou Anaconda)

Tendo isso instalado, verifique se o comando `conda` está acessível no seu *shell*.
Clone o repositório:
```shell
$ git clone git@github.com:LQCAPF/PDE.git
```

Acesse a pasta `backend` na raiz do repositório e lance um terminal.

Crie o ambiente do conda:
```shell
$ conda env create -f environment.yml
```

E então ative o ambiente. Isso precisa ser feito sempre que você abrir um novo terminal:
```shell
$ conda activate PDE
```

Com isso feito, o projeto está configurado. Execute o arquivo principal (pelo menos até criarmos um `Makefile`):
```shell
$ python pde/main.py
```

#### Extensões recomendadas (para usuários de VSCode)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) para habilitar o suporte completo ao Python no VSCode (recomendo também ativar o autoformatter, usando o `autopep8`);
- [TodoTree](https://marketplace.visualstudio.com/items?itemName=Gruntfuggly.todo-tree) para sumarizar todos os `TODO`s colocados no código;
