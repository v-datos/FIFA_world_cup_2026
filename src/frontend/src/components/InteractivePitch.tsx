import React, { useState } from 'react';

interface Player {
  name: string;
  position: string;
  club?: string;
}

interface InteractivePitchProps {
  teamName: string;
  flag?: string;
  players: string[];
  formation: string;
  lang: string;
}

const PLAYER_CLUBS_ALL: Record<string, string> = {
  // Netherlands
  "Cody Gakpo": "Liverpool", "Memphis Depay": "Corinthians", "Virgil van Dijk": "Liverpool",
  "Nathan Aké": "Manchester City", "Nathan Ake": "Manchester City", "Matthijs de Ligt": "Manchester United",
  "Denzel Dumfries": "Inter Milan", "Jeremie Frimpong": "Bayer Leverkusen", "Stefan de Vrij": "Inter Milan",
  "Micky van de Ven": "Tottenham Hotspur", "Tijjani Reijnders": "AC Milan", "Jerdy Schouten": "PSV Eindhoven",
  "Joey Veerman": "PSV Eindhoven", "Xavi Simons": "RB Leipzig", "Donyell Malen": "Borussia Dortmund",
  "Wout Weghorst": "Ajax", "Brian Brobbey": "Ajax", "Joshua Zirkzee": "Manchester United",
  // Japan
  "Kaoru Mitoma": "Brighton & Hove Albion", "Takefusa Kubo": "Real Sociedad", "Wataru Endo": "Liverpool",
  "Hidemasa Morita": "Sporting CP", "Daichi Kamada": "Crystal Palace", "Ritsu Doan": "SC Freiburg",
  "Takumi Minamino": "Monaco", "Keito Nakamura": "Reims", "Ko Itakura": "Borussia Mönchengladbach",
  "Koki Machida": "Union SG", "Shogo Taniguchi": "Sint-Truiden", "Yukinari Sugawara": "Southampton",
  "Zion Suzuki": "Parma", "Ayase Ueda": "Feyenoord", "Daizen Maeda": "Celtic", "Takuma Asano": "Mallorca",
  // Ivory Coast
  "Franck Kessié": "Al-Ahli", "Sébastien Haller": "Leganés", "Simon Adingra": "Brighton & Hove Albion",
  "Nicolas Pépé": "Villarreal", "Ibrahim Sangaré": "Nottingham Forest", "Seko Fofana": "Al-Ettifaq",
  "Odilon Kossounou": "Atalanta", "Evan Ndicka": "Roma", "Serge Aurier": "Galatasaray", "Yahia Fofana": "Angers",
  // Ecuador
  "Moisés Caicedo": "Chelsea", "Enner Valencia": "Internacional", "Piero Hincapié": "Bayer Leverkusen",
  "Pervis Estupiñán": "Brighton & Hove Albion", "Willian Pacho": "Paris Saint-Germain",
  "Kendry Páez": "Independiente del Valle", "Jeremy Sarmiento": "Burnley", "Félix Torres": "Corinthians",
  "Alexander Domínguez": "LDU Quito",
  // Sweden
  "Alexander Isak": "Newcastle United", "Dejan Kulusevski": "Tottenham Hotspur", "Viktor Gyökeres": "Sporting CP",
  "Emil Forsberg": "New York Red Bulls", "Victor Lindelöf": "Manchester United", "Ludwig Augustinsson": "Anderlecht",
  "Robin Olsen": "Aston Villa", "Anthony Elanga": "Nottingham Forest", "Jens Cajuste": "Ipswich Town",
  // Tunisia
  "Ellyes Skhiri": "Eintracht Frankfurt", "Youssef Msakni": "Al-Arabi", "Hannibal Mejbri": "Burnley",
  "Aissa Laïdouni": "Al-Wakrah", "Montassar Talbi": "Lorient", "Wajdi Kechrida": "Standard Liège",
  "Ali Abdi": "Nice", "Bechir Ben Said": "Espérance de Tunis", "Elias Achouri": "Copenhagen",
  // Spain
  "Lamine Yamal": "Barcelona", "Nico Williams": "Athletic Bilbao", "Rodri": "Manchester City",
  "Pedri": "Barcelona", "Dani Olmo": "Barcelona", "Álvaro Morata": "AC Milan", "Alvaro Morata": "AC Milan",
  "Dani Carvajal": "Real Madrid", "Robin Le Normand": "Atlético Madrid", "Unai Simón": "Athletic Bilbao",
  "Unai Simon": "Athletic Bilbao", "Fabián Ruiz": "Paris Saint-Germain", "Fabian Ruiz": "Paris Saint-Germain",
  // Cape Verde
  "Ryan Mendes": "Kocaelispor", "Garry Rodrigues": "Sivasspor", "Jovane Cabral": "Estrela da Amadora",
  "Logan Costa": "Villarreal", "Bebé": "Racing Ferrol", "Bebe": "Racing Ferrol", "Jamiro Monteiro": "PEC Zwolle",
  "Kenny Rocha Santos": "AEZ Zakakiou", "Roberto Lopes": "Shamrock Rovers",
  // Belgium
  "Kevin De Bruyne": "Manchester City", "Romelu Lukaku": "Napoli", "Jérémy Doku": "Manchester City",
  "Jeremy Doku": "Manchester City", "Lois Openda": "RB Leipzig", "Leandro Trossard": "Arsenal",
  "Amadou Onana": "Aston Villa", "Youri Tielemans": "Aston Villa", "Wout Faes": "Leicester City",
  "Timothy Castagne": "Fulham", "Koen Casteels": "Al-Qadsiah",
  // Egypt
  "Mohamed Salah": "Liverpool", "Mostafa Mohamed": "Nantes", "Omar Marmoush": "Eintracht Frankfurt",
  "Trezeguet": "Al-Rayyan", "Mohamed Elneny": "Al-Jazira", "Emam Ashour": "Al Ahly",
  "Mohamed Hany": "Al Ahly", "Ahmed Hegazi": "Neom", "Mohamed Abou Gabal": "National Bank of Egypt",
  // Saudi Arabia
  "Salem Al-Dawsari": "Al-Hilal", "Firas Al-Buraikan": "Al-Ahli", "Abdulrahman Ghareeb": "Al-Nassr",
  "Mohamed Kanno": "Al-Hilal", "Faisal Al-Ghamdi": "Beerschot", "Saud Abdulhamid": "Roma",
  "Ali Al-Bulaihi": "Al-Hilal", "Yasser Al-Shahrani": "Al-Hilal", "Mohammed Al-Owais": "Al-Hilal",
  // Uruguay
  "Darwin Núñez": "Liverpool", "Darwin Nunez": "Liverpool", "Luis Suárez": "Inter Miami", "Luis Suarez": "Inter Miami",
  "Federico Valverde": "Real Madrid", "Facundo Pellistri": "Panathinaikos", "Manuel Ugarte": "Manchester United",
  "Nicolas de la Cruz": "Flamengo", "Nicolas Tagliafico": "Lyon", "Ronald Araújo": "Barcelona", "Ronald Araujo": "Barcelona",
  "Mathías Olivera": "Napoli", "Mathias Olivera": "Napoli", "Jose María Giménez": "Atlético Madrid", "Sergio Rochet": "Internacional",
  // Iran
  "Mehdi Taremi": "Inter Milan", "Sardar Azmoun": "Shabab Al-Ahli", "Alireza Jahanbakhsh": "Heerenveen",
  "Saman Ghoddos": "Ittihad Kalba", "Mehdi Ghayedi": "Ittihad Kalba", "Saeid Ezatolahi": "Shabab Al-Ahli",
  "Milad Mohammadi": "Persepolis", "Shojae Khalilzadeh": "Tractor", "Alireza Beiranvand": "Tractor",
  "Hossein Kanaanizadegan": "Persepolis", "Ramin Rezaeian": "Esteghlal", "Mehdi Torabi": "Tractor",
  // New Zealand
  "Chris Wood": "Nottingham Forest", "Sarpreet Singh": "Unattached", "Liberato Cacace": "Empoli",
  "Joe Bell": "Viking", "Marko Stamenic": "Olympiacos", "Tyler Bindon": "Reading",
  "Michael Boxall": "Minnesota United", "Alex Paulsen": "Auckland FC", "Nando Pijnaker": "Sligo Rovers",
  "Bill Tuiloma": "Charlotte FC", "Matthew Garbett": "NAC Breda", "Elijah Just": "Horsens",
  // France
  "Kylian Mbappé": "Real Madrid", "Kylian Mbappe": "Real Madrid", "Antoine Griezmann": "Atlético Madrid",
  "Ousmane Dembélé": "Paris Saint-Germain", "Ousmane Dembele": "Paris Saint-Germain", "Marcus Thuram": "Inter Milan",
  "Bradley Barcola": "Paris Saint-Germain", "Aurélien Tchouaméni": "Real Madrid", "Aurelien Tchouameni": "Real Madrid",
  "Eduardo Camavinga": "Real Madrid", "N'Golo Kanté": "Al-Ittihad", "N'Golo Kante": "Al-Ittihad",
  "William Saliba": "Arsenal", "Dayot Upamecano": "Bayern Munich", "Theo Hernández": "AC Milan",
  "Theo Hernandez": "AC Milan", "Jules Koundé": "Barcelona", "Jules Kounde": "Barcelona", "Mike Maignan": "AC Milan",
  // Senegal
  "Sadio Mané": "Al-Nassr", "Sadio Mane": "Al-Nassr", "Nicolas Jackson": "Chelsea", "Ismaïla Sarr": "Crystal Palace",
  "Ismaila Sarr": "Crystal Palace", "Iliman Ndiaye": "Everton", "Lamine Camara": "Monaco", "Pape Matar Sarr": "Tottenham Hotspur",
  "Pape Sarr": "Tottenham Hotspur", "Kalidou Koulibaly": "Al-Hilal", "Abdou Diallo": "Al-Arabi",
  "Moussa Niakhaté": "Lyon", "Édouard Mendy": "Al-Ahli", "Edouard Mendy": "Al-Ahli", "Formose Mendy": "Lorient",
  "Abdoulaye Seck": "Maccabi Haifa", "Ismail Jakobs": "Galatasaray", "Idrissa Gueye": "Everton",
  // Iraq
  "Aymen Hussein": "Al-Khor", "Ali Jasim": "Como", "Mohanad Ali": "Al-Shorta", "Ibrahim Bayesh": "Al-Riyadh",
  "Youssef Amyn": "Al-Wehda", "Amir Al-Ammari": "Cracovia", "Osama Rashid": "Free Agent", "Saad Natiq": "Al-Shorta",
  "Rebin Sulaka": "FC Seoul", "Jalal Hassan": "Al-Zawraa", "Hussein Ali": "Heerenveen", "Merchas Doski": "Slovácko",
  // Norway
  "Erling Haaland": "Manchester City", "Martin Ødegaard": "Arsenal", "Martin Odegaard": "Arsenal",
  "Alexander Sørloth": "Atlético Madrid", "Alexander Sorloth": "Atlético Madrid", "Antonio Nusa": "RB Leipzig",
  "Oscar Bobb": "Manchester City", "Sander Berge": "Fulham", "Patrick Berg": "Bodø/Glimt",
  "Julian Ryerson": "Borussia Dortmund", "Leo Østigård": "Rennes", "Leo Ostigard": "Rennes",
  "Andreas Hanche-Olsen": "Mainz 05", "Ørjan Nyland": "Sevilla", "Orjan Nyland": "Sevilla",
  "David Wolfe": "AZ Alkmaar", "Kristoffer Ajer": "Brentford",
  // Algeria
  "Riyad Mahrez": "Al-Ahli", "Baghdad Bounedjah": "Al-Shamal", "Amine Gouiri": "Rennes", "Said Benrahma": "Lyon",
  "Houssem Aouar": "Al-Ittihad", "Ismaël Bennacer": "AC Milan", "Ismael Bennacer": "AC Milan", "Nabil Bentaleb": "Lille",
  "Ramy Bensebaini": "Borussia Dortmund", "Aïssa Mandi": "Lille", "Aissa Mandi": "Lille",
  "Rayan Aït-Nouri": "Wolverhampton Wanderers", "Rayan Ait-Nouri": "Wolverhampton Wanderers", "Anthony Mandrea": "Caen",
  "Youcef Atal": "Al-Sadd", "Fares Chaibi": "Eintracht Frankfurt",
  // Austria
  "Marcel Sabitzer": "Borussia Dortmund", "Konrad Laimer": "Bayern Munich", "Christoph Baumgartner": "RB Leipzig",
  "Romano Schmid": "Werder Bremen", "Michael Gregoritsch": "SC Freiburg", "Florian Grillitsch": "TSG Hoffenheim",
  "Nicolas Seiwald": "RB Leipzig", "Stefan Posch": "Bologna", "Kevin Danso": "Lens", "Maximilian Wöber": "Leeds United",
  "Maximilian Wober": "Leeds United", "Patrick Pentz": "Brøndby", "Phillipp Mwene": "Mainz 05", "Patrick Wimmer": "Wolfsburg",
  // Jordan
  "Musa Al-Taamari": "Montpellier", "Yazan Al-Naimat": "Al-Ahli SC", "Ali Olwan": "Selangor",
  "Mahmoud Al-Mardi": "Al-Hussein Irbid", "Nizar Al-Rashdan": "Emirates Club", "Noor Al-Rawabdeh": "Selangor",
  "Yazan Al-Arab": "FC Seoul", "Abdallah Nasib": "Al-Hussein Irbid", "Salem Al-Ajalin": "Al-Faisaly",
  "Yazid Abu Layla": "Al-Jabalain", "Yazeed Abulaila": "Al-Jabalain", "Ehsan Haddad": "Al-Faisaly"
};

export const InteractivePitch: React.FC<InteractivePitchProps> = ({
  teamName,
  flag,
  players,
  formation,
  lang,
}) => {
  const [hoveredPlayer, setHoveredPlayer] = useState<string | null>(null);

  const getCoordinates = (index: number, total: number, lineIndex: number, totalLines: number) => {
    const y = 10 + (lineIndex / (totalLines - 1)) * 80;
    const x = 10 + ((index + 1) / (total + 1)) * 80;
    return { x, y };
  };

  const categorizePlayers = () => {
    const gk: Player[] = [];
    const df: Player[] = [];
    const mf: Player[] = [];
    const fw: Player[] = [];

    const defCount = parseInt(formation.split('-')[0]) || 4;
    const midCount = parseInt(formation.split('-')[1]) || 3;

    players.forEach((pName, idx) => {
      const pData: Player = {
        name: pName,
        position: 'Player',
        club: PLAYER_CLUBS_ALL[pName] || 'Free Agent',
      };

      if (idx === 0) {
        pData.position = lang === 'Español' ? 'Portero' : 'Goalkeeper';
        gk.push(pData);
      } else if (idx <= defCount) {
        pData.position = lang === 'Español' ? 'Defensor' : 'Defender';
        df.push(pData);
      } else if (idx <= defCount + midCount) {
        pData.position = lang === 'Español' ? 'Centrocampista' : 'Midfielder';
        mf.push(pData);
      } else {
        pData.position = lang === 'Español' ? 'Delantero' : 'Forward';
        fw.push(pData);
      }
    });

    return [gk, df, mf, fw].filter((arr) => arr.length > 0);
  };

  const lines = categorizePlayers();
  const totalLines = lines.length;

  const translateLabel = (text: string) => {
    if (lang === 'English') return text;
    const map: Record<string, string> = {
      'Club': 'Club',
      'Position': 'Posición',
    };
    return map[text] || text;
  };

  return (
    <div className="w-full flex flex-col items-center">
      <div className="text-center mb-4">
        <h4 className="text-lg font-semibold text-slate-100">{flag ? `${flag} ` : ''}{teamName}</h4>
        <span className="text-sm text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 font-mono">
          {formation}
        </span>
      </div>

      {/* Styled Tactical Football Pitch */}
      <div className="relative w-full max-w-[420px] aspect-[3/4] bg-emerald-950/20 border-2 border-emerald-500/30 rounded-xl shadow-2xl">
        {/* Pitch markings */}
        <div className="absolute inset-x-0 top-0 h-1/2 border-b border-emerald-500/20" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 border border-emerald-500/20 rounded-full" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-emerald-500/30 rounded-full" />
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-48 h-20 border-x border-b border-emerald-500/20" />
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-24 h-8 border-x border-b border-emerald-500/20" />
        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 w-48 h-20 border-x border-t border-emerald-500/20" />
        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 w-24 h-8 border-x border-t border-emerald-500/20" />

        {/* Players mapping */}
        {lines.map((linePlayers, lineIdx) => (
          <React.Fragment key={lineIdx}>
            {linePlayers.map((player, pIdx) => {
              const { x, y } = getCoordinates(pIdx, linePlayers.length, lineIdx, totalLines);
              const isHovered = hoveredPlayer === player.name;

              return (
                <div
                  key={player.name}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer ${isHovered ? 'z-50' : 'z-10'}`}
                  style={{ left: `${x}%`, bottom: `${y}%` }}
                  onMouseEnter={() => setHoveredPlayer(player.name)}
                  onMouseLeave={() => setHoveredPlayer(null)}
                >
                  {/* Player Dot */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shadow-lg transition-all duration-200 border-2 ${
                      isHovered
                        ? 'bg-emerald-400 border-emerald-100 text-slate-950 scale-125 shadow-emerald-500/40'
                        : 'bg-slate-900 border-emerald-500/80 text-emerald-400'
                    }`}
                  >
                    {player.name.substring(0, 2).toUpperCase()}
                  </div>

                  {/* Player Name Tag (sits BELOW the dot so it never overlaps) */}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 whitespace-nowrap bg-slate-950/85 text-[10px] text-slate-200 px-1.5 py-0.5 rounded border border-slate-800/50">
                    {player.name.split(' ').pop()}
                  </div>

                  {/* Player Info Card */}
                  {isHovered && (
                    <div className="absolute left-10 top-0 -translate-y-1/3 w-52 bg-slate-950/98 border border-slate-700 rounded-lg p-3 shadow-2xl z-50 pointer-events-none">
                      <div className="font-bold text-sm text-slate-100">{player.name}</div>
                      <div className="text-xs text-emerald-400 font-medium mb-1.5">{player.position}</div>
                      <div className="text-[11px] text-slate-400">
                        <strong className="text-slate-300 font-medium">{translateLabel('Club')}:</strong>{' '}
                        {player.club}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
