import type { ConfigTableRow } from "../configEditorModel";

export interface ConfigDraft{
    id: string;
    fileName: string;
    savedAt: number;
    originalConfig: unknown;
    configRows: Record<string, ConfigTableRow[]>;
    selectedMenu: string;
}

const STORAGE_KEY = "config-editor:drafts:v1";

//  This read th ConfigDraft list, which holds all of the drafts fo the current session
function readDrafts(): ConfigDraft[]{
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (!stored) return [];

    const parsed: unknown = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
        throw new Error("The saved configuration drafts have an invalid format.");
    }
    return parsed as ConfigDraft[];
}

//  Key for the draft that is currently selected. 
const ACTIVE_DRAFT_KEY = "config-editor:active-draft:v1";


export const configDraftController = {

//  lists all of the drafts
    list(): ConfigDraft[] {
        return readDrafts();
    },


//  saves a draft of all of the values in the currrent page
    save(draft: ConfigDraft): void {
        const drafts = readDrafts().filter((item) => item.id !== draft.id);
        sessionStorage.setItem(
            STORAGE_KEY,
            JSON.stringify([...drafts, { ...draft, savedAt: Date.now() }]),
         );
    },

//  sets the id of the active draft
    setActiveId(id: string): void {
        sessionStorage.setItem(ACTIVE_DRAFT_KEY, id);
    },

//  removes a draft from the list of drafts
    remove(id: string): void {
        const drafts = readDrafts().filter((draft) => draft.id !== id);
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));

        if (sessionStorage.getItem(ACTIVE_DRAFT_KEY) === id) {
        sessionStorage.removeItem(ACTIVE_DRAFT_KEY);
        }
    },
};


