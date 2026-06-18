import teamIdentityData from '../../../../data/reference/team_identity.json';

export interface TeamIdentity {
  team_id: string;
  display_name: string;
  slug: string;
  flag: string;
  aliases: string[];
}

const TEAM_IDENTITIES = teamIdentityData as TeamIdentity[];

const fold = (value: string): string =>
  value
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const slugifyRaw = (value: string): string =>
  value
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');

const aliasIndex = new Map<string, TeamIdentity>();
const slugIndex = new Map<string, TeamIdentity>();

TEAM_IDENTITIES.forEach((identity) => {
  [identity.display_name, identity.slug, ...identity.aliases].forEach((name) => {
    aliasIndex.set(fold(name), identity);
    aliasIndex.set(slugifyRaw(name), identity);
    slugIndex.set(slugifyRaw(name), identity);
  });
});

export const normalizeTeamName = (team: string): string => {
  const identity = aliasIndex.get(fold(team));
  return identity?.display_name || team.trim();
};

export const teamSlug = (team: string): string => {
  const identity = aliasIndex.get(fold(team));
  return identity?.slug || slugifyRaw(team);
};

export const getTeamIdentity = (team: string): TeamIdentity | null =>
  aliasIndex.get(fold(team)) || null;

export const getTeamNameById = (teamId: string | number): string | null => {
  const identity = TEAM_IDENTITIES.find((team) => team.team_id === String(teamId));
  return identity?.display_name || null;
};

export const getTeamFlag = (team: string): string | null =>
  getTeamIdentity(team)?.flag || null;

export { TEAM_IDENTITIES };
