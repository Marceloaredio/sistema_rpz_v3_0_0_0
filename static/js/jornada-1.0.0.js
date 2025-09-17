let blocoAtual = 0;

function navegarBloco(delta) {
    const blocos = document.querySelectorAll('.bloco-dia');
    blocos[blocoAtual].style.display = 'none';
    blocoAtual += delta;
    blocoAtual = Math.max(0, Math.min(blocos.length - 1, blocoAtual));
    blocos[blocoAtual].style.display = 'block';
}

// Outras funções relacionadas com a lógica de manipulação de dados e visualização
function toggleCamposHorarios(selectElement) {
    const container = selectElement.closest("div").querySelector(".campos-horarios");
    const motivo = selectElement.value;
    
    // Verificar se estamos na página de análise de fechamento
    const isClosureAnalysis = window.location.pathname.includes('closure_analysis') || 
                              window.location.pathname.includes('closure-analysis') ||
                              document.querySelector('.bloco-dia .campo-observacao option[value="GARAGEM"]');
    
    console.log('toggleCamposHorarios:', {
        motivo: motivo,
        isClosureAnalysis: isClosureAnalysis,
        container: container
    });
    
    if (isClosureAnalysis && (motivo === "GARAGEM" || motivo === "CARGA/DESCARGA")) {
        // Na análise de fechamento, mostrar campos para GARAGEM e CARGA/DESCARGA
        container.style.display = "block";
        console.log(`Mostrando campos para ${motivo} na análise de fechamento`);
    } else if (motivo === "Definir horário") {
        // Na análise de jornada, mostrar campos para "Definir horário"
        container.style.display = "block";
        console.log('Mostrando campos para "Definir horário" na análise de jornada');
    } else {
        container.style.display = "none";
        console.log('Ocultando campos de horário');
    }
}

function calcularTempoParada(inicio, fim) {
    if (!inicio || !fim) return "00:00";
    const [h1, m1] = inicio.split(":").map(Number);
    const [h2, m2] = fim.split(":").map(Number);
    const t1 = new Date(0, 0, 0, h1, m1);
    const t2 = new Date(0, 0, 0, h2, m2);
    let diff = (t2 - t1) / 1000;
    if (diff < 0) diff += 86400;
    const horas = Math.floor(diff / 3600);
    const minutos = Math.floor((diff % 3600) / 60);
    return `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}`;
}

function atualizarTempoParadaNaLinha(linha) {
    const inicio = linha.querySelector('.campo-inicio');
    const fim = linha.querySelector('.campo-fim');
    const tempo = linha.querySelector('.campo-tempo');
    if (inicio && fim && tempo) {
        tempo.value = calcularTempoParada(inicio.value, fim.value);
    }
}

function configurarEventosTempoParada() {
    document.querySelectorAll("tbody tr").forEach(linha => {
        const inicio = linha.querySelector('.campo-inicio');
        const fim = linha.querySelector('.campo-fim');
        if (inicio) inicio.addEventListener("input", () => atualizarTempoParadaNaLinha(linha));
        if (fim) fim.addEventListener("input", () => atualizarTempoParadaNaLinha(linha));
    });
}


function salvarAnalise(motorist_id, plate) {
    const blocos = document.querySelectorAll('.bloco-dia');
    let erros = [];

    blocos.forEach((bloco, index) => {
        const tituloBloco = bloco.querySelector('h2')?.innerText || `Bloco ${index + 1}`;
        const alerta = bloco.querySelector('.campos-horarios');

        if (alerta) {
            const motivo = bloco.querySelector('select')?.value;
            if (!motivo) erros.push(`${tituloBloco}: selecione um motivo.`);
        } else {
            const tables = bloco.querySelectorAll("table.tabela-jornada");

            const inicioSelects = [tables[0], tables[1]].map(tbl => tbl?.querySelector("select")).filter(Boolean);
            const fimSelects = [tables[2], tables[3]].map(tbl => tbl?.querySelector("select")).filter(Boolean);

            const validosInicio = inicioSelects.filter(s => s.value === "Válido").length;
            const validosFim = fimSelects.filter(s => s.value === "Válido").length;

            if (validosInicio !== 1) erros.push(`${tituloBloco}: selecione apenas UM início de jornada válido.`);
            if (validosFim !== 1) erros.push(`${tituloBloco}: selecione apenas UM fim de jornada válido.`);

            const tabelaParadas = tables[4];
            const selectsParadas = Array.from(tabelaParadas?.querySelectorAll("select") || []);
            const validacoes = selectsParadas.map(sel => sel.value).filter(v => v && v.trim() !== "");

            // Filtrar apenas os itens "REFEIÇÃO"
            const refeicoes = validacoes.filter(v => v === "REFEIÇÃO");

            // Verificar se "REFEIÇÃO" foi duplicado
            if (refeicoes.length > 1) {
                erros.push(`${tituloBloco}: o item "REFEIÇÃO" não pode ser duplicado.`);
            }
        }
    });

    if (erros.length > 0) {
        alert("Erros encontrados:\n\n" + erros.join("\n"));
        return;
    }

    gerarTabelaConfirmacao(motorist_id, plate);
}

function getMotoristaId() {
    // Tenta obter o motorist_id do elemento com data-motorist-id
    const motoristElement = document.querySelector('[data-motorist-id]');
    if (motoristElement && motoristElement.dataset.motoristId) {
        return motoristElement.dataset.motoristId;
    }
    
    // Se não encontrar, tenta obter da URL
    const urlParams = new URLSearchParams(window.location.search);
    const motoristId = urlParams.get('motorist_id');
    if (motoristId) {
        return motoristId;
    }
    
    // Se ainda não encontrou, procura em outros elementos possíveis
    const hiddenInput = document.querySelector('input[name="motorist_id"]');
    if (hiddenInput && hiddenInput.value) {
        return hiddenInput.value;
    }
    
    console.warn("Não foi possível encontrar o ID do motorista");
    return null;
}

function atualizarDados(motorist_id) {
    if (!motorist_id) {
        motorist_id = getMotoristaId();
        if (!motorist_id) {
            console.error("ID do motorista não encontrado");
            return;
        }
    }
    
    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Primeiro atualiza os cálculos
    atualizarCalculos();
    
    // Depois atualiza o interstício
    atualizarIntersticio();

    // Espera um pouco para garantir que os cálculos foram atualizados
    wait(1000).then(() => {
        // Por fim atualiza as infrações
        atualizarInfractions(motorist_id);
    });
}

function gerarTabelaConfirmacao(motorist_id, plate) {
    const tabela = document.getElementById("tabela-confirmacao");
    tabela.innerHTML = "";  // Limpa a tabela para evitar duplicação de conteúdo

    const blocos = document.querySelectorAll('.bloco-dia');
    const headersFixas = [
        "Placa", "Data", "Dia da Semana",
        "Início Jornada", "In. Refeição", "Fim Refeição",
        "Fim de Jornada", "Observação",
        "Tempo Refeição", "Interstício", "Tempo Intervalo", "Tempo Carga/Descarga",
        "Jornada Total", "Tempo Direção", "Direção sem Pausa"
    ];
    const headersExtras = [];
    for (let i = 1; i <= 8; i++) headersExtras.push(`In. Descanso ${i}`, `Fim Descanso ${i}`);
    for (let i = 1; i <= 7; i++) headersExtras.push(`In. Car/Desc ${i}`, `Fim Car/Desc ${i}`);

    // Verifica/cria <tbody>
    let tbody = tabela.querySelector("tbody");
    if (!tbody) {
        tbody = document.createElement("tbody");
    } else {
        tbody.innerHTML = '';
    }

    const linhasTemp = [];
    let fimJornadaAnterior = null;

    // Funções auxiliares de tempo
    const tempoMin = s => {
        if (!s || !s.includes(":")) return 0;
        const [h, m] = s.split(":").map(Number);
        return h * 60 + m;
    };
    const tempoFormat = m => {
        const hh = String(Math.floor(m / 60)).padStart(2, '0');
        const mm = String(m % 60).padStart(2, '0');
        return `${hh}:${mm}`;
    };
    const calcDiff = (ini, fim) => {
        if (!ini || !fim) return "00:00";
        const diff = tempoMin(fim) - tempoMin(ini);
        return tempoFormat(diff >= 0 ? diff : diff + 1440);
    };
    const sumAll = arr => tempoFormat(
        arr.reduce((tot, p) => tot + Math.max(0, tempoMin(p.fim) - tempoMin(p.ini)), 0)
    );

    // Insere registros anteriores na tabela
    function adicionarRegistrosAnteriores(registros) {
        registros.forEach(linha => {
            const tr = document.createElement("tr");
            tr.classList.add('old-line');

            // Definir os campos principais do registro
            const lf = {
                "Placa": linha.placa || "",
                "Data": linha.data || "",
                "Dia da Semana": linha.dia_da_semana || "",
                "Início Jornada": linha.inicio_jornada || "",
                "In. Refeição": linha.in_refeicao || "",
                "Fim Refeição": linha.fim_refeicao || "",
                "Fim de Jornada": linha.fim_jornada || "",
                "Observação": linha.observacao || "",
                "Tempo Refeição": linha.tempo_refeicao || "",
                "Interstício": linha.intersticio || "",
                "Tempo Intervalo": linha.tempo_intervalo || "",
                "Tempo Carga/Descarga": linha.tempo_carga_descarga || "",
                "Jornada Total": linha.jornada_total || "",
                "Tempo Direção": linha.tempo_direcao || "",
                "Direção sem Pausa": linha.direcao_sem_pausa || ""
            };

            // Processa descansos
            const descansos = [];
            for (let i = 1; i <= 8; i++) {
                if (linha[`in_descanso_${i}`]) {
                    descansos.push({
                        ini: linha[`in_descanso_${i}`],
                        fim: linha[`fim_descanso_${i}`]
                    });
                }
            }

            // Processa cargas/descargas
            const cargas = [];
            for (let i = 1; i <= 7; i++) {
                if (linha[`in_car_desc_${i}`]) {
                    cargas.push({
                        ini: linha[`in_car_desc_${i}`],
                        fim: linha[`fim_car_desc_${i}`]
                    });
                }
            }

            // Processa refeições
            const refeicoes = [];
            if (linha.in_refeicao && linha.fim_refeicao) {
                refeicoes.push({
                    ini: linha.in_refeicao,
                    fim: linha.fim_refeicao
                });
            }

            // Adiciona os descansos nas colunas correspondentes
            descansos.forEach((d, i) => {
                lf[`In. Descanso ${i + 1}`] = d.ini || " ";
                lf[`Fim Descanso ${i + 1}`] = d.fim || " ";
            });

            // Adiciona as cargas/descargas nas colunas correspondentes
            cargas.forEach((c, i) => {
                lf[`In. Car/Desc ${i + 1}`] = c.ini || " ";
                lf[`Fim Car/Desc ${i + 1}`] = c.fim || " ";
            });

            const headersFixas = [
                "Placa", "Data", "Dia da Semana",
                "Início Jornada", "In. Refeição", "Fim Refeição",
                "Fim de Jornada", "Observação",
                "Tempo Refeição", "Interstício", "Tempo Intervalo", "Tempo Carga/Descarga",
                "Jornada Total", "Tempo Direção", "Direção sem Pausa"
            ];
            const headersExtras = [];
            for (let i = 1; i <= 8; i++) headersExtras.push(`In. Descanso ${i}`, `Fim Descanso ${i}`);
            for (let i = 1; i <= 7; i++) headersExtras.push(`In. Car/Desc ${i}`, `Fim Car/Desc ${i}`);

            [...headersFixas, ...headersExtras].forEach(col => {
                const td = document.createElement("td");
                td.textContent = lf[col] || "";
                if (col === "Data") td.setAttribute("data-col", "Data");
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    }

    // Descobre a data mais antiga
    let dataMaisAntiga = null;
    blocos.forEach((bloco, index) => {
        const h2 = bloco.querySelector("h2")?.innerText || "";
        const data = h2.split(" - ")[1]?.split(" (")[0] || "";
        if (!dataMaisAntiga || new Date(data) < new Date(dataMaisAntiga)) {
            dataMaisAntiga = data;
        }
    });

    console.log("dataMaisAntiga", dataMaisAntiga);

    // Busca 7 registros anteriores
    $.ajax({
        url: `/api/retrieve_n_records_before_date?target_date=${dataMaisAntiga}&n=7&motorist_id=${motorist_id}`,
        method: 'GET',
        success: function(data) {
            adicionarRegistrosAnteriores(data.reverse());

            // Monta linhas atuais
            blocos.forEach(bloco => {
                const valorObservacao = bloco.querySelector('.campo-observacao')?.value || "";
                const obs = valorObservacao.toLowerCase().includes("definir") ? "" : valorObservacao;
                const placa = obs.toLowerCase() === "folga" ? "Folga" : plate;
                const h2 = bloco.querySelector("h2")?.innerText || "";
                const data = h2.split(" - ")[1]?.split(" (")[0] || "";
                const dia = abreviarDiaSemana(h2.split(" (")[1]?.replace(")", "") || "");

                // Variáveis de início e fim de jornada
                let inicioJornada = "", fimJornada = "", inRef = "", fimRef = "";
                const descansos = [];
                const cargas = [];
                const refeicoes = [];

                // Verificando se há campos de horários ou não
                const isSemMovimento = bloco.querySelector(".campos-horarios");
                if (isSemMovimento) {
                    const inputs = bloco.querySelectorAll(".campos-horarios input");
                    [inicioJornada, inRef, fimRef, fimJornada] = Array.from(inputs).map(i => i.value);
                } else {
                    const tables = bloco.querySelectorAll("table.tabela-jornada");
                    const inicioSelects = [tables[0], tables[1]].map(tbl => tbl?.querySelector("select")).filter(Boolean);
                    const fimSelects = [tables[2], tables[3]].map(tbl => tbl?.querySelector("select")).filter(Boolean);

                    // Verifica se os selects têm valor "Válido" e preenche os horários
                    inicioSelects.forEach(sel => {
                        if (sel.value === "Válido") inicioJornada = sel.closest("tr").querySelector("input[type='time']")?.value || "";
                    });
                    fimSelects.forEach(sel => {
                        if (sel.value === "Válido") fimJornada = sel.closest("tr").querySelector("input[type='time']")?.value || "";
                    });

                    // Processa as paradas de descanso, refeição e carga/descarga
                    const linhasParadas = bloco.querySelectorAll("table:last-of-type tbody tr");
                    linhasParadas.forEach(l => {
                        const tipo = l.querySelector("select")?.value || "";
                        const ini = l.querySelector(".campo-inicio")?.value || "";
                        const fim = l.querySelector(".campo-fim")?.value || "";

                        if (tipo.includes("REFEIÇÃO")) {
                            inRef = ini;
                            fimRef = fim;
                        }
                        if (tipo.includes("REFEIÇÃO") && ini && fim) refeicoes.push({ini, fim});
                        if (tipo.includes("DESCANSO") && ini && fim) descansos.push({ini, fim});
                        if (tipo.includes("CARGA/DESCARGA") && ini && fim) cargas.push({ini, fim});
                    });
                }

                // cálculos
                const refeicao = calcDiff(inRef, fimRef);
                const intersticio = fimJornadaAnterior ? calcDiff(fimJornadaAnterior, inicioJornada) : "00:00";
                const totalDesc = sumAll(descansos);
                const totalCD = sumAll(cargas);
                const horasJornada = calcDiff(inicioJornada, fimJornada);

                const jornadaMin = tempoMin(horasJornada);
                const almocoMin = tempoMin(refeicao);
                const descMin = tempoMin(totalDesc);
                const cm = tempoMin(totalCD);

                // Tempo Direção
                const direcaoMin = Math.max(0, jornadaMin - almocoMin - descMin - cm);
                const horasDirecao = tempoFormat(direcaoMin);

                // Direção sem Pausa (maior período de direção contínua)
                const t0 = tempoMin(inicioJornada), tf = tempoMin(fimJornada);
                let pausas = [...descansos, ...cargas, ...refeicoes]  // Incluindo refeição
                    .map(p => ({ini: tempoMin(p.ini), fim: tempoMin(p.fim)}))
                    .filter(p => p.ini < p.fim && p.fim > t0 && p.ini < tf)
                    .map(p => ({
                        ini: Math.max(p.ini, t0),
                        fim: Math.min(p.fim, tf)
                    }))
                    .sort((a, b) => a.ini - b.ini);

                // Calcular intervalo de direção contínua
                let prevEnd = t0, maxGap = 0;
                pausas.forEach(p => {
                    const gap = p.ini - prevEnd; // intervalo de direção
                    if (gap > maxGap) maxGap = gap;
                    if (p.fim > prevEnd) prevEnd = p.fim;
                });
                const finalGap = tf - prevEnd;
                if (finalGap > maxGap) maxGap = finalGap;

                const direcaoSemPausa = tempoFormat(maxGap);

                fimJornadaAnterior = fimJornada;

                // Preenche os dados na linha
                const linhaFinal = {
                    "Placa": placa,
                    "Data": data,
                    "Dia da Semana": dia,
                    "Início Jornada": inicioJornada,
                    "In. Refeição": inRef,
                    "Fim Refeição": fimRef,
                    "Fim de Jornada": fimJornada,
                    "Observação": obs,
                    "Tempo Refeição": refeicao,
                    "Interstício": intersticio,
                    "Tempo Intervalo": totalDesc,
                    "Tempo Carga/Descarga": totalCD,
                    "Jornada Total": horasJornada,
                    "Tempo Direção": horasDirecao,
                    "Direção sem Pausa": direcaoSemPausa
                };

                descansos.forEach((d, i) => {
                    linhaFinal[`In. Descanso ${i + 1}`] = d.ini;
                    linhaFinal[`Fim Descanso ${i + 1}`] = d.fim;
                });
                cargas.forEach((c, i) => {
                    linhaFinal[`In. Car/Desc ${i + 1}`] = c.ini;
                    linhaFinal[`Fim Car/Desc ${i + 1}`] = c.fim;
                });

                const linhaDOM = document.createElement("tr");
                linhaDOM.classList.add("new-line");
                [...headersFixas, ...headersExtras].forEach(col => {
                    const td = document.createElement("td");
                    td.textContent = linhaFinal[col] || "";
                    if (col === "Data") td.setAttribute("data-col", "Data");
                    linhaDOM.appendChild(td);
                });
                linhasTemp.push(linhaDOM);
            });

            // Cabeçalho
            const thead = document.createElement("thead");
            const headRow = document.createElement("tr");
            [...headersFixas, ...headersExtras].forEach(h => {
                const th = document.createElement("th");
                th.textContent = h;
                headRow.appendChild(th);
            });
            thead.appendChild(headRow);
            tabela.appendChild(thead);

            // Adiciona as linhas na tabela
            linhasTemp.forEach(l => tbody.appendChild(l));
            tabela.appendChild(tbody);

            // Adiciona evento de duplo clique nas células da tabela
            tabela.addEventListener('dblclick', function(e) {
                const td = e.target.closest('td');
                if (!td) return;
                
                // Verifica se é uma linha antiga (não editável)
                if (td.closest('tr').classList.contains('old-line')) return;
                
                const colIndex = td.cellIndex;
                const colName = headersFixas[colIndex];
                
                // Lista de campos protegidos (não editáveis)
                const camposProtegidos = [
                    "Placa", "Data", "Dia da Semana", "Observação",
                    "Tempo Refeição", "Interstício", "Tempo Intervalo",
                    "Tempo Carga/Descarga", "Jornada Total", "Tempo Direção", 
                    "Direção sem Pausa"
                ];
                
                // Verifica se o campo é protegido
                if (camposProtegidos.includes(colName)) return;
                
                const valor = td.textContent;
                const input = document.createElement('input');
                input.value = valor;
                input.style.width = '100%';
                input.style.boxSizing = 'border-box';
                
                // Verifica se é um campo de tempo
                if (colName && (
                    colName.includes("Início") || 
                    colName.includes("In.") || 
                    colName.includes("Fim") || 
                    colName.toLowerCase().includes("hora")
                )) {
                    input.type = 'time';
                } else {
                    input.type = 'text';
                }
                
                td.textContent = '';
                td.appendChild(input);
                input.focus();
                
                input.addEventListener('blur', function() {
                    td.textContent = this.value;
                    atualizarCalculos();
                    // Depois atualiza as infrações
                    const motorist_id = getMotoristaId();
                    if (motorist_id) {
                        console.log("Atualizando dados...");
                        atualizarDados(motorist_id);
                    } else {
                        console.error("ID do motorista não encontrado");
                    }
                });
                
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        this.blur();
                    }
                });
            });

            document.getElementById("modal-confirmacao").style.display = "flex";
        },
        error: function() {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro ao buscar registros anteriores.'
            });
        }
    });

    atualizarDados(motorist_id);
}

let attempts = 0;  // Inicialize 'attempts' fora da função para que ela tenha um valor inicial
const maxAttempts = 5;  // Número máximo de tentativas
const retryDelay = 1000;  // Delay de 1 segundo (1000ms) entre as tentativas

function calcularIntersticio(inicioDataHora, fimDataHoraAnterior) {
    const inicio = new Date(inicioDataHora); // Cria um objeto Date para o início da jornada
    const fim = new Date(fimDataHoraAnterior); // Cria um objeto Date para o fim da jornada anterior

    // Calcula a diferença em milissegundos
    const diffMs = inicio - fim;

    // Se a diferença for NaN (quando algum dos dados não é válido), retorna "00:00"
    if (isNaN(diffMs)) {
        return "00:00";  // Retorna "00:00" se o cálculo não for válido
    }

    // Converte para minutos
    const diffMinutos = Math.abs(diffMs) / (1000 * 60);

    // Calcula as horas e minutos
    const horas = Math.floor(diffMinutos / 60);
    const minutos = Math.round(diffMinutos % 60);

    return `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}`;
}

// Função principal para calcular o interstício
async function tryFindLinhas() {
    const tabelasLinhas = document.querySelectorAll("#tabela-confirmacao tbody tr");

    if (tabelasLinhas.length === 0) {
        // Se não encontrou as linhas, tenta novamente
        if (attempts < maxAttempts) {
            attempts++;
            console.log(`Tentativa ${attempts} de encontrar as linhas...`);
            setTimeout(() => tryFindLinhas(), retryDelay); // Tenta novamente após 1 segundo
        } else {
            console.log("Não foi possível encontrar as linhas após várias tentativas.");
        }
        return; // Retorna para não executar o restante do código caso não tenha encontrado as linhas
    }

    // Se as linhas foram encontradas, processar o interstício
    tabelasLinhas.forEach((linha, index) => {
        const dataStr = linha.cells[1].textContent.trim(); // A célula "Data" está na 2ª coluna (índice 1)
        const inicioJornada = linha.cells[3].textContent.trim(); // "Início Jornada" está na 4ª coluna (índice 3)
        const fimJornada = linha.cells[6].textContent.trim(); // "Fim de Jornada" está na 7ª coluna (índice 6)
        const intersticioCell = linha.cells[9]; // "Interstício" está na 10ª coluna (índice 9)

        // Se a data, inicio jornada ou fim jornada não estiverem presentes, retorne "00:00"
        if (!dataStr || !inicioJornada || !fimJornada) {
            intersticioCell.textContent = "00:00";
            return;
        }

        // Converte a data para o formato yyyy-mm-dd
        const dataArray = dataStr.split("-");  // Separa a data no formato dd-mm-yyyy
        const dataFormatada = `${dataArray[2]}-${dataArray[1]}-${dataArray[0]}`; // Converte para yyyy-mm-dd

        // Verifica se é a primeira linha
        if (index === 0) {
            // Se for a primeira linha, o interstício é 00:00
            intersticioCell.textContent = "00:00";
            return;
        }

        // Busca o "Fim de Jornada" da linha anterior válida (não folga)
        const fimJornadaAnteriorLinha = obterFimJornadaValida(linha, index, tabelasLinhas);
        const dataAnterior = obterDataDaLinhaAnteriorValida(linha, index, tabelasLinhas);

        if (!fimJornadaAnteriorLinha || !dataAnterior) {
            intersticioCell.textContent = "00:00"; // Se não encontrar o fim de jornada da linha anterior, retorna 00:00
        } else {
            // Agora dividimos a data e hora para o cálculo de interstício
            const inicioDataHora = `${dataFormatada} ${inicioJornada}`;  // Combina a data de início com o horário atual
            const fimDataHoraAnterior = `${dataAnterior} ${fimJornadaAnteriorLinha}`; // Combina a data da linha anterior com o horário de fim anterior

            // Calcula o interstício com base na data e hora combinadas
            const intersticio = calcularIntersticio(inicioDataHora, fimDataHoraAnterior);

            intersticioCell.textContent = intersticio;  // Atualiza o valor do interstício
        }
    });
}

function obterDataDaLinhaAnteriorValida(linha, index, tabelasLinhas) {
    // Loop para procurar a linha anterior até encontrar dados válidos (não folga)
    while (index > 0) {
        const linhaAnterior = tabelasLinhas[index - 1];

        const inicioJornadaAnterior = linhaAnterior.cells[3].textContent.trim(); // Coluna "Início Jornada"
        const fimJornadaAnterior = linhaAnterior.cells[6].textContent.trim(); // Coluna "Fim Jornada"
        const observacaoAnterior = linhaAnterior.cells[7].textContent.trim(); // Coluna "Observação"

        // Se a linha anterior tiver início e fim de jornada válidos E não for folga, retorna a data dela
        if (inicioJornadaAnterior && fimJornadaAnterior && observacaoAnterior.toLowerCase() !== "folga") {
            const dataStrAnterior = linhaAnterior.cells[1].textContent.trim(); // A célula "Data" está na 2ª coluna (índice 1)
            const dataArray = dataStrAnterior.split("-");  // Separa a data no formato dd-mm-yyyy
            return `${dataArray[2]}-${dataArray[1]}-${dataArray[0]}`; // Converte para yyyy-mm-dd
        }

        index--; // Vai para a linha anterior
    }

    // Se chegar até a primeira linha sem encontrar dados válidos, retorna uma string vazia
    return "";
}

// Função para buscar o "Fim de Jornada" da linha anterior válida (não folga)
function obterFimJornadaValida(linha, index, tabelasLinhas) {
    // Loop para procurar a linha anterior até encontrar dados válidos (não folga)
    while (index > 0) {
        const linhaAnterior = tabelasLinhas[index - 1];

        const inicioJornadaAnterior = linhaAnterior.cells[3].textContent.trim(); // Coluna "Início Jornada"
        const fimJornadaAnterior = linhaAnterior.cells[6].textContent.trim(); // Coluna "Fim Jornada"
        const observacaoAnterior = linhaAnterior.cells[7].textContent.trim(); // Coluna "Observação"

        // Se a linha anterior tiver início e fim de jornada válidos E não for folga, retorna o fim da jornada
        if (inicioJornadaAnterior && fimJornadaAnterior && observacaoAnterior.toLowerCase() !== "folga") {
            return fimJornadaAnterior;
        }

        index--; // Vai para a linha anterior
    }

    // Se chegar até a primeira linha sem encontrar dados válidos, retorna uma string vazia
    return "";
}

async function atualizarIntersticio() {
    await tryFindLinhas(); // Inicia a tentativa de encontrar as linhas e calcular o interstício
}

async function atualizarInfractions(motorist_id) {
    try {
        // Espera a Promise de extrairTabelaComoJSON se resolver
        const tabelaJSON = await extrairTabelaComoJSON(false); // Espera que a função retorne o JSON

        // Cria o payload com o JSON extraído
        const payload = {
            motorist_id: motorist_id,
            tabela: JSON.parse(tabelaJSON)  // Faz o JSON.parse se o JSON for retornado como string
        };

        let attempts = 0; // Contador de tentativas
        const maxAttempts = 5; // Número máximo de tentativas
        const retryDelay = 1000; // Delay de 1 segundo (1000ms) entre as tentativas

        // Função para tentar novamente até o número máximo de tentativas
        async function tryFetchInfractions() {
            try {
                // Fazendo o request para pegar as infrações novamente com o payload
                const response = await fetch('/api/get-infractions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });
                const infractions = await response.json();  // Recebe a resposta JSON

                // Cria um array com as datas das infrações
                const infractionsDates = infractions.map(infracao => infracao.date);

                // Verifique se a tabela está carregada
                const linhas = document.querySelectorAll("#tabela-confirmacao tbody tr");

                if (linhas.length === 0) {
                    // Se não encontrou as linhas, tenta novamente
                    if (attempts < maxAttempts) {
                        attempts++;
                        setTimeout(tryFetchInfractions, retryDelay); // Tenta novamente após 1 segundo
                    } else {
                        console.error("Não foi possível carregar as linhas após várias tentativas.");
                    }
                    return; // Retorna para não executar o restante do código caso não tenha encontrado as linhas
                }

                // Se as linhas forem encontradas, processar as infrações
                linhas.forEach(linha => {
                    // Verifica se a linha tem a classe 'new-line'
                    if (linha.classList.contains('new-line')) {
                        const data = linha.querySelector("td[data-col='Data']").textContent.trim();  // Remover espaços extras na data

                        // Verifica se a data da linha está nas infrações
                        if (infractionsDates.includes(data)) {
                            linha.classList.add("has_infraction");  // Adiciona a classe 'has_infraction'

                            // Encontrar as infrações correspondentes à data
                            const infractionsForDate = infractions.filter(infracao => infracao.date === data);

                            // Concatenar todas as infrações no tooltip
                            const infractionTypes = Array.isArray(infractionsForDate) ? infractionsForDate.map(infracao => infracao.infraction_desc) : [infractionsForDate.infraction_desc];

                            linha.title = `Infração(s):\n${infractionTypes.join("\n")}`;

                        } else {
                            linha.classList.remove("has_infraction");  // Remove a classe 'has_infraction' se não houver infração
                            linha.title = "";  // Limpa o tooltip se não houver infração
                        }

                        // Forçar a atualização visual, caso a classe tenha sido removida
                        linha.style.transition = "none"; // Desativa a transição, para evitar efeitos visuais temporários
                        linha.offsetHeight; // Força o "reflow" do layout, garantindo que a classe seja removida corretamente
                        linha.style.transition = ""; // Restaura a transição
                    }
                });
            } catch (error) {
                console.error("Erro ao buscar infrações:", error);
            }
        }

        // Iniciar a busca de infrações
        tryFetchInfractions();
    } catch (error) {
        console.error("Erro ao extrair tabela:", error);
    }
}

function tempoParaMinutos(hhmm) {
    if (!hhmm || !hhmm.includes(":")) return 0;
    const [h, m] = hhmm.split(":").map(Number);
    return h * 60 + m;
}

function minutosParaTempo(min) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function atualizarCalculos() {
    const linhas = document.querySelectorAll("#tabela-confirmacao tbody tr");
    const headers = Array.from(document.querySelectorAll("#tabela-confirmacao th")).map(th => th.textContent.trim());

    linhas.forEach((linha, i) => {
        const get = (col) => {
            const idx = headers.indexOf(col);
            const input = linha.querySelectorAll("td")[idx]?.querySelector("input");
            return input ? input.value : linha.querySelectorAll("td")[idx]?.textContent.trim();
        };

        const set = (col, valor) => {
            const idx = headers.indexOf(col);
            const cell = linha.querySelectorAll("td")[idx];
            if (cell && !cell.querySelector("input")) {
                const valorAnterior = cell.textContent.trim();
                if (valorAnterior !== valor) {
                    cell.textContent = valor;
                    cell.style.transition = "background-color 0.4s ease";
                    cell.style.backgroundColor = "#fff7aa";  // Destaque amarelinho
                    setTimeout(() => {
                        cell.style.backgroundColor = "";
                    }, 800);
                }
            }
        };

        // Cálculo do tempo de refeição
        const tRef = tempoParaMinutos(get("Fim Refeição")) - tempoParaMinutos(get("In. Refeição"));
        set("Tempo Refeição", minutosParaTempo(tRef > 0 ? tRef : 0));

        // Cálculo do tempo total de descanso (intervalos)
        let totalDescanso = 0;
        for (let d = 1; d <= 8; d++) {
            const ini = get(`In. Descanso ${d}`);
            const fim = get(`Fim Descanso ${d}`);
            if (ini && fim) {
                totalDescanso += Math.max(0, tempoParaMinutos(fim) - tempoParaMinutos(ini));
            }
        }
        set("Tempo Intervalo", minutosParaTempo(totalDescanso));

        // Cálculo do tempo total de carga/descarga
        let totalCD = 0;
        for (let c = 1; c <= 7; c++) {
            const ini = get(`In. Car/Desc ${c}`);
            const fim = get(`Fim Car/Desc ${c}`);
            if (ini && fim) {
                totalCD += Math.max(0, tempoParaMinutos(fim) - tempoParaMinutos(ini));
            }
        }
        set("Tempo Carga/Descarga", minutosParaTempo(totalCD));

        // Cálculo da duração da jornada
        const iniJornada = tempoParaMinutos(get("Início Jornada"));
        const fimJornada = tempoParaMinutos(get("Fim de Jornada"));
        let duracao = fimJornada - iniJornada;
        if (duracao < 0) duracao += 1440;
        const horasJornada = Math.max(0, duracao);
        set("Jornada Total", minutosParaTempo(horasJornada));

        // Cálculo do tempo de direção
        const horasDirecao = Math.max(0, horasJornada - totalCD - totalDescanso - tRef);
        set("Tempo Direção", minutosParaTempo(horasDirecao));

        // Cálculo da Direção sem Pausa (maior intervalo de direção ininterrupta)
        const pausas = [];
        for (let d = 1; d <= 8; d++) {
            const iniDescanso = get(`In. Descanso ${d}`);
            const fimDescanso = get(`Fim Descanso ${d}`);
            if (iniDescanso && fimDescanso) {
                pausas.push({ini: tempoParaMinutos(iniDescanso), fim: tempoParaMinutos(fimDescanso)});
            }
        }

        for (let c = 1; c <= 7; c++) {
            const iniCarDesc = get(`In. Car/Desc ${c}`);
            const fimCarDesc = get(`Fim Car/Desc ${c}`);
            if (iniCarDesc && fimCarDesc) {
                pausas.push({ini: tempoParaMinutos(iniCarDesc), fim: tempoParaMinutos(fimCarDesc)});
            }
        }

        // Adicionando refeição à lista de pausas
        const inRef = get("In. Refeição");
        const fimRef = get("Fim Refeição");
        if (inRef && fimRef) {
            pausas.push({ini: tempoParaMinutos(inRef), fim: tempoParaMinutos(fimRef)});
        }

        // Ordenar pausas por início
        pausas.sort((a, b) => a.ini - b.ini);

        // Calcular os intervalos de direção
        let maxDirecaoSemPausa = 0;
        let prevFim = iniJornada;

        pausas.forEach(pausa => {
            const intervaloDirecao = pausa.ini - prevFim;
            if (intervaloDirecao > maxDirecaoSemPausa) {
                maxDirecaoSemPausa = intervaloDirecao;
            }
            prevFim = pausa.fim;
        });

        // Considerar o final da jornada como uma pausa
        const intervaloFinal = fimJornada - prevFim;
        if (intervaloFinal > maxDirecaoSemPausa) {
            maxDirecaoSemPausa = intervaloFinal;
        }

        // Atualizar o campo "Direção sem Pausa"
        set("Direção sem Pausa", minutosParaTempo(maxDirecaoSemPausa));

        // Atualizar a placa para "Folga" se for o caso
        if (get("Observação")?.toLowerCase() === "folga") {
            set("Placa", "Folga");
        }
    });

    atualizarIntersticio();
}


function abreviarDiaSemana(diaCompleto) {
    const mapa = {
        "Segunda-feira": "Seg.",
        "Terça-feira": "Ter.",
        "Quarta-feira": "Qua.",
        "Quinta-feira": "Qui.",
        "Sexta-feira": "Sex.",
        "Sábado": "Sáb.",
        "Domingo": "Dom."
    };
    return mapa[diaCompleto] || diaCompleto;
}

function extrairTabelaComoJSON(newOnly = false) {
    return new Promise((resolve, reject) => {
        const tabela = document.getElementById("tabela-confirmacao");

        if (!tabela) {
            console.error("Tabela não encontrada!");
            reject("Tabela não encontrada");
            return;
        }

        // Função para verificar se as linhas estão carregadas
        const checkTableLoaded = () => {
            const linhas = newOnly
                ? tabela.querySelectorAll("tbody tr.new-line")  // Somente as linhas com a classe 'new-line'
                : tabela.querySelectorAll("tbody tr");  // Pega todas as linhas

            // Se as linhas estiverem carregadas
            if (linhas.length > 0) {
                const headers = Array.from(tabela.querySelectorAll("thead th")).map(th => th.innerText.trim());

                const dados = Array.from(linhas).map(tr => {
                    const colunas = tr.querySelectorAll("td");
                    const linhaObj = {};

                    headers.forEach((header, index) => {
                        if (header !== "➕") {
                            const celula = colunas[index];
                            if (celula) {
                                // Se a célula tem um input, pegar o value do input
                                const input = celula.querySelector('input');
                                if (input) {
                                    linhaObj[header] = input.value || "";
                                } else {
                                    linhaObj[header] = celula.innerText.trim() || "";
                                }
                            } else {
                                linhaObj[header] = "";
                            }
                        }
                    });

                    return linhaObj;
                });

                resolve(JSON.stringify(dados, null, 2));  // Resolva a Promise com o JSON bem formatado
            } else {
                console.log("Aguardando as linhas carregarem...");
                setTimeout(checkTableLoaded, 500); // Re-executa a verificação a cada 500ms
            }
        };

        // Inicia a verificação das linhas
        checkTableLoaded();
    });
}

async function enviarTabelaComoJSON(motorist_id, motorist_name, truck_id, plate, acao = "salvar") {
    try {
        // Extrair todos os registros (incluindo antigos) para cálculo correto de infrações
        const tabelaCompletaJSON = await extrairTabelaComoJSON(false);
        const tabelaCompleta = JSON.parse(tabelaCompletaJSON);
        
        // Extrair apenas os registros novos para salvar
        const tabelaNovosJSON = await extrairTabelaComoJSON(true);
        const tabelaNovos = JSON.parse(tabelaNovosJSON);
        
        // Identificar quais registros são novos (para salvar apenas esses)
        const datasNovas = tabelaNovos.map(registro => registro.Data);
        
        // Marcar registros como novos ou antigos
        const tabelaProcessada = tabelaCompleta.map(registro => ({
            ...registro,
            is_new_record: datasNovas.includes(registro.Data)
        }));

        // Cria o payload com todos os dados (para cálculo de infrações) e marcação de novos
        const payload = {
            motorist_id: motorist_id,
            motorist_name: motorist_name,
            truck_id: truck_id,
            plate: plate,
            acao: acao,
            tabela: tabelaProcessada,
            datas_novas: datasNovas  // Lista de datas que devem ser salvas
        };

        // Função para fazer o envio
        function enviarDados(substituir = false) {
            if (substituir) {
                payload.substituir = true;
            }

            return new Promise((resolve, reject) => {
                $.ajax({
                    url: "/api/save-table",
                    method: "POST",
                    contentType: "application/json",
                    data: JSON.stringify(payload),
                    statusCode: {
                        // Trata 409 como um caso especial, não como erro
                        409: function(jqXHR) {
                            const response = jqXHR.responseJSON;
                            const conflitos = response.conflitos_detalhados || response.conflitos || [];
                            
                            // Usar a função utilitária para mostrar conflitos formatados
                            showConflictModal(conflitos, function() {
                                // Se confirmou, envia novamente com substituir=true
                                enviarDados(true)
                                    .then(resolve)
                                    .catch(reject);
                            }, function() {
                                resolve(false); // Usuário cancelou
                            });
                        }
                    },
                    success: function(response) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: response.mensagem || 'Dados salvos!'
                        }).then(() => {
                            window.location.href = "/track";
                        });
                        resolve(true);
                    },
                    error: function(jqXHR) {
                        // Apenas outros erros que não sejam 409
                        if (jqXHR.status !== 409) {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erro',
                                text: 'Erro ao salvar dados.'
                            });
                            reject(new Error('Erro ao salvar dados'));
                        }
                    }
                });
            });
        }

        // Faz o primeiro envio
        await enviarDados();

    } catch (err) {
        console.error("Erro ao enviar tabela:", err);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: err.message || 'Falha ao salvar dados'
        });
    }
}