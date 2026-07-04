import { normalizeTeamName } from './teamIdentity';

export const TEAM_TRANSLATIONS_ES: Record<string, string> = {
  "Argentina": "Argentina", "Algeria": "Argelia", "Austria": "Austria", "Jordan": "Jordania",
  "Belgium": "Bélgica", "Egypt": "Egipto", "Canada": "Canadá", "Qatar": "Catar",
  "Czechia": "Chequia", "Czech Republic": "República Checa", "South Africa": "Sudáfrica", "England": "Inglaterra",
  "Croatia": "Croacia", "France": "Francia", "Senegal": "Senegal", "Ghana": "Ghana",
  "Panama": "Panamá", "Iran": "Irán", "New Zealand": "Nueva Zelanda", "Iraq": "Irak",
  "Norway": "Noruega", "Mexico": "México", "South Korea": "Corea del Sur", "Portugal": "Portugal",
  "DR Congo": "RDC", "Democratic Republic of the Congo": "República Democrática del Congo", "Saudi Arabia": "Arabia Saudita",
  "Uruguay": "Uruguay", "Spain": "España", "Cape Verde": "Cabo Verde", "Switzerland": "Suiza",
  "Bosnia and Herzegovina": "Bosnia y Herzegovina", "Brazil": "Brasil", "Morocco": "Marruecos",
  "Haiti": "Haití", "Scotland": "Escocia", "United States": "Estados Unidos", "Paraguay": "Paraguay",
  "Australia": "Australia", "Turkiye": "Turquía", "Turkey": "Turquía", "Germany": "Alemania",
  "Curacao": "Curazao", "Ivory Coast": "Costa de Marfil", "Ecuador": "Ecuador", "Japan": "Japón",
  "Sweden": "Suecia", "Tunisia": "Túnez", "Uzbekistan": "Uzbekistán", "Colombia": "Colombia",
  "Bosnia": "Bosnia"
};

export const translateTeamName = (team: string, lang: string): string => {
  if (lang !== 'Español' || !team) return team;
  const normalized = normalizeTeamName(team);
  return TEAM_TRANSLATIONS_ES[normalized] || TEAM_TRANSLATIONS_ES[team] || team;
};

export const translateInjury = (inj: string, lang: string): string => {
  if (lang !== 'Español' || !inj) return inj;
  if (inj === 'No major injuries reported.' || inj === 'No confirmed injuries reported.') {
    return 'Sin lesiones confirmadas reportadas.';
  }
  if (inj === 'No verified baseline injury update is available yet.') {
    return 'Sin actualización de lesiones disponible aún.';
  }
  
  let translated = inj;
  
  // Statuses
  translated = translated
    .replace(/ - Out\)/g, ' - Baja)')
    .replace(/ - Doubtful\)/g, ' - Duda)')
    .replace(/ - Probable\)/g, ' - Probable)')
    .replace(/ - Cleared to play\)/g, ' - De alta)');

  // Common injury reasons
  translated = translated
    .replace(/broken collarbone/gi, 'clavícula rota')
    .replace(/calf injury/gi, 'lesión de pantorrilla')
    .replace(/muscle tear/gi, 'desgarro muscular')
    .replace(/fitness concerns/gi, 'problemas de condición física')
    .replace(/concussion/gi, 'conmoción cerebral')
    .replace(/hamstring injury/gi, 'lesión de isquiotibiales')
    .replace(/hamstring problem/gi, 'problema de isquiotibiales')
    .replace(/hamstring tear/gi, 'desgarro de isquiotibiales')
    .replace(/hamstring/gi, 'isquiotibiales')
    .replace(/foot fracture/gi, 'fractura de pie')
    .replace(/foot injury/gi, 'lesión de pie')
    .replace(/ankle injury/gi, 'lesión de tobillo')
    .replace(/knee injury/gi, 'lesión de rodilla')
    .replace(/groin injury/gi, 'lesión de ingle')
    .replace(/groin/gi, 'ingle')
    .replace(/thigh strain/gi, 'distensión de muslo')
    .replace(/adductor injury/gi, 'lesión de aductores')
    .replace(/medial ligament/gi, 'ligamento medial')
    .replace(/physical issue/gi, 'problema físico')
    .replace(/minor knock/gi, 'golpe menor')
    .replace(/illness/gi, 'enfermedad')
    .replace(/suspension/gi, 'suspensión')
    .replace(/red card/gi, 'tarjeta roja');

  return translated;
};

export const translatePhilosophy = (phil: string | null | undefined, lang: string): string => {
  if (!phil) return '';
  if (lang !== 'Español') return phil;

  const map: Record<string, string> = {
    "Confirmed XI from ESPN match data.": "XI confirmado de los datos del partido de ESPN.",
    "Baseline tactical preview pending.": "Vista previa táctica inicial pendiente.",
    "Positional overload with fluid movement around Lionel Messi.": "Sobrecarga posicional con movimiento fluido alrededor de Lionel Messi.",
    "Compact defensive block with quick direct counters through Amoura and Gouiri.": "Bloque defensivo compacto con contragolpes rápidos y directos a través de Amoura y Gouiri.",
    "High-intensity vertical press and immediate counter-pressing.": "Presión vertical de alta intensidad y contrapresión inmediata.",
    "Deep low-block with quick transitions through Al-Taamari.": "Bloque bajo profundo con transiciones rápidas a través de Al-Taamari.",
    "Fluid, high-tempo attacking transitions orchestrated by Kevin De Bruyne.": "Transiciones de ataque fluidas y de alto ritmo orquestadas por Kevin De Bruyne.",
    "Highly organized defensive mid-block with quick direct plays to Salah and Marmoush.": "Bloque medio defensivo muy organizado con jugadas rápidas y directas para Salah y Marmoush.",
    "Aggressive high press and direct vertical attacking transitions.": "Presión alta agresiva y transiciones de ataque verticales directas.",
    "Compact defensive block springing direct counters through Akram Afif.": "Bloque defensivo compacto con contragolpes directos a través de Akram Afif.",
    "Direct vertical play focusing on aerial duels and high-volume crossing.": "Juego vertical directo centrado en duelos aéreos y centros de alto volumen.",
    "High-tempo technical passing with a structured low-block transition focus.": "Pases técnicos de alto ritmo con un enfoque estructurado de transición en bloque bajo.",
    "Tuchel's structured possession with positional fullbacks and direct wide threats.": "Posesión estructurada de Tuchel con laterales posicionales y amenazas abiertas directas.",
    "Veteran midfield tempo control built around Modric and Kovacic possession cycles.": "Control de ritmo del mediocampo veterano construido alrededor de los ciclos de posesión de Modric y Kovacic.",
    "High-transition direct attacking built around Mbappe and a fluid front line.": "Ataque directo de alta transición construido al rededor de Mbappé y una línea delantera fluida.",
    "High-intensity pressing with rapid wing transitions through Mane and Diatta.": "Presión de alta intensidad con transiciones rápidas por las bandas a través de Mané y Diatta.",
    "Fast vertical transition utilizing Kudus' ball-carrying ability.": "Transición vertical rápida utilizando la capacidad de transporte de balón de Kudus.",
    "Direct, physical CONCACAF football with an organized low block and set-piece focus.": "Fútbol físico y directo de CONCACAF con un bloque bajo organizado y enfoque en jugadas a balón parado.",
    "Pragmatic defensive setup with reliance on captain Mehdi Taremi's link-up quality.": "Configuración defensiva pragmática con confianza en la calidad de asociación del capitán Mehdi Taremi.",
    "Direct attacking focusing on crossing and aerial dominance through Chris Wood.": "Ataque directo centrado en centros y dominio aéreo a través de Chris Wood.",
    "Disciplined, defensively organized mid-block with a focal-point target man.": "Bloque medio disciplinado y organizado defensivamente con un hombre objetivo como punto focal.",
    "Aggressive high press with direct vertical balls into Haaland's central runs.": "Presión alta agresiva con balones verticales directos hacia las carreras centrales de Haaland.",
    "High intensity pressing, vertical transitions, and dynamic flank overloads.": "Presión de alta intensidad, transiciones verticales y sobrecargas dinámicas por las bandas.",
    "Compact defensive organization, direct flank crosses, and set-piece targeting.": "Organización defensiva compacta, centros directos por las bandas y objetivos a balón parado."
  };

  return map[phil] || phil;
};

export const translateStanding = (standing: string | null, lang: string): string => {
  if (!standing) return 'N/A';
  if (lang !== 'Español') return standing;
  
  let translated = standing;
  translated = translated
    .replace(/Semi-finals/g, 'Semifinales')
    .replace(/Quarter-finals/g, 'Cuartos de final')
    .replace(/Round of 16/g, 'Octavos de final')
    .replace(/Runners-up/g, 'Subcampeón')
    .replace(/Did not qualify/g, 'No clasificó')
    .replace(/Fourth Place/g, 'Cuarto lugar')
    .replace(/Third Place/g, 'Tercer lugar')
    .replace(/Champions/g, 'Campeón')
    .replace(/Group Stage/g, 'Fase de grupos')
    .replace(/Africa Cup of Nations/g, 'Copa Africana de Naciones')
    .replace(/UEFA Nations League/g, 'Liga de Naciones de la UEFA')
    .replace(/OFC Nations Cup/g, 'Copa de Naciones de la OFC')
    .replace(/CONCACAF Gold Cup/g, 'Copa Oro de la CONCACAF')
    .replace(/UEFA European Championship|Euro/g, 'Eurocopa')
    .replace(/AFC Asian Cup|Asian Cup/g, 'Copa Asiática')
    .replace(/Gold Cup/g, 'Copa Oro')
    .replace(/FIFA World Cup|World Cup/g, 'Copa del Mundo');
  return translated;
};

export const translateSimMessage = (msg: string | undefined, lang: string): string | undefined => {
  if (!msg) return undefined;
  if (lang !== 'Español') return msg;

  let translated = msg;
  translated = translated
    .replace(/Random-trial Monte Carlo simulation with/gi, 'Simulación Monte Carlo de ensayos aleatorios con')
    .replace(/trials and seed/gi, 'ensayos y semilla')
    .replace(/Ratings use/gi, 'Las calificaciones usan')
    .replace(/world_football_elo/gi, 'World Football Elo')
    .replace(/hardcoded_reference/gi, 'referencia local');
  return translated;
};

export const translateBriefingMessage = (msg: string | undefined, lang: string): string | undefined => {
  if (!msg) return undefined;
  if (lang !== 'Español') return msg;

  const map: Record<string, string> = {
    "Fresh source-backed match briefing is available.": "El briefing fresco respaldado por fuentes está disponible.",
    "Fresh briefing artifact is available, but it is not source-backed match research.": "El briefing fresco está disponible, pero no está respaldado por investigación de fuentes.",
    "Briefing artifact exists but its validity window has expired.": "El briefing existe pero su ventana de validez ha expirado.",
    "Briefing artifact exists but is outside the configured last-minute window.": "El briefing existe pero está fuera de la ventana de último minuto configurada.",
    "Briefing generation was blocked; use the static baseline preview until inputs are resolved.": "La generación del briefing fue bloqueada; use la vista previa estática hasta resolver los insumos.",
    "Briefing generation was skipped for this fixture.": "La generación del briefing fue omitida para este partido.",
    "Briefing artifact exists but is invalid; use the static baseline preview.": "El briefing existe pero es inválido; use la vista previa estática.",
    "Static baseline preview only; no last-minute briefing has been generated.": "Vista previa estática base solamente; no se ha generado un briefing de último minuto."
  };

  return map[msg] || msg;
};

export const translateSourceLabel = (label: string | undefined, lang: string): string | undefined => {
  if (!label) return undefined;
  const clean = label.replace(/_/g, ' ').toLowerCase();
  if (lang !== 'Español') return clean;

  const map: Record<string, string> = {
    "live schedule": "calendario en vivo",
    "static curated": "curado estático",
    "generated model": "modelo generado",
    "default forecast": "pronóstico predeterminado",
    "hardcoded reference": "referencia local",
    "proxy historical": "partido proxy",
    "web researched": "investigado en la web",
    "missing": "no disponible",
    "blocked": "bloqueado",
    "fotmob": "FotMob",
    "espn derived": "derivado de ESPN",
    "derived": "derivado",
    "ai web grounded": "IA investigado en la web",
    "ai generated": "IA generado"
  };

  return map[clean] || clean;
};

export const translateStage = (stage: string | null | undefined, lang: string): string => {
  if (!stage) return '';
  if (lang !== 'Español') return stage;

  let translated = stage;
  translated = translated
    .replace(/Group Stage - Group/g, 'Fase de grupos - Grupo')
    .replace(/Group Stage/g, 'Fase de grupos')
    .replace(/Round of 32/g, 'Dieciseisavos de final')
    .replace(/Round of 16/g, 'Octavos de final')
    .replace(/Quarterfinal/g, 'Cuartos de final')
    .replace(/Semifinal/g, 'Semifinal')
    .replace(/Third Place/g, 'Tercer lugar')
    .replace(/Final/g, 'Final');
  return translated;
};

