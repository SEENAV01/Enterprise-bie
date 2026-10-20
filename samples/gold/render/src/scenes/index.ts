import React from "react";
import { Hook } from "./hook";
import { Title } from "./title";
import { CellBuild } from "./cell";
import { Division } from "./division";
import { Ladder, TissueTeam } from "./tissue";
import { GrowthCompare, MeristemZoom } from "./growth";
import { Bridge, ExamTraps, PlantZones, SummaryTable } from "./zones";

export const SCENES: Record<string, React.FC> = {
  Hook, Title, CellBuild, Division, TissueTeam, Ladder, GrowthCompare, MeristemZoom, PlantZones, SummaryTable, ExamTraps, Bridge,
};
