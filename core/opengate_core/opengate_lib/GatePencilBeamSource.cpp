/* --------------------------------------------------
   Copyright (C): OpenGate Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#include "GatePencilBeamSource.h"
#include "G4IonTable.hh"
#include "GateHelpersDict.h"
#include <G4UnitsTable.hh>

GatePencilBeamSource::GatePencilBeamSource() : GateGenericSource() {}

GatePencilBeamSource::~GatePencilBeamSource() = default;

void GatePencilBeamSource::CreateSPS() {
  fSPS_PB = new GateSingleParticleSourcePencilBeam(std::string(), fMother);
  fSPS = fSPS_PB;
}

void GatePencilBeamSource::PrepareNextRun() {
  // The following compute the global transformation from
  // the local volume (mother) to the world
  GateVSource::PrepareNextRun();
  // This global transformation is given to the SPS that will
  // generate particles in the correct coordinate system
  // translation
  fSPS_PB->SetSourceRotTransl(fGlobalTranslation, fGlobalRotation);
}

void GatePencilBeamSource::InitializeDirection(py::dict puser_info) {
  // GateGenericSource::InitializeDirection(puser_info);
  //  PBS parameters
  auto dir_info = py::dict(puser_info["direction"]);
  fSPS_PB->SetPBSourceParam(dir_info);

  // angle acceptance ?
  auto d = py::dict(puser_info["direction"]);
  auto dd = py::dict(d["acceptance_angle"]);
  fAAManager.Initialize(dd, false);
  if (fAAManager.IsEnabled()) {
    Fatal("Sorry, cannot use Acceptance Angle with Pencil Beam source (yet).");
  }
}
