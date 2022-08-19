/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#ifndef GateHitsCollectionActor_h
#define GateHitsCollectionActor_h

#include <pybind11/stl.h>
#include "GateVActor.h"
#include "GateHitsCollection.h"

namespace py = pybind11;

class GateHitsCollectionActor : public GateVActor {

public:

    explicit GateHitsCollectionActor(py::dict &user_info);

    virtual ~GateHitsCollectionActor();

    // Called when the simulation start (master thread only)
    void StartSimulationAction() override;

    // Called every time a Run starts (all threads)
    void BeginOfRunAction(const G4Run *run) override;

    // Called every time an Event starts
    void BeginOfEventAction(const G4Event * event) override;

    // Called every time a batch of step must be processed
    void SteppingAction(G4Step * /*unused*/) override;

    // Called every time a Run ends (all threads)
    void EndOfRunAction(const G4Run *run) override;

    // Called by every worker when the simulation is about to end
    void EndOfSimulationWorkerAction(const G4Run * /*lastRun*/) override;

    // Called when the simulation end (master thread only)
    void EndSimulationAction() override;


protected:
    std::string fOutputFilename;
    std::string fHitsCollectionName;
    std::vector<std::string> fUserHitAttributeNames;
    GateHitsCollection *fHits;
    bool fDebug;
    int fClearEveryNEvents;

};

#endif // GateHitsCollectionActor_h