CREATE OR REPLACE FUNCTION DropBusTables ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP TABLE BusLeg;
    DROP FUNCTION CallIndexIsWithinJourney;
    DROP TABLE BusVehicle;
    DROP TABLE BusModel;
    DROP TABLE BusCall;
    DROP TABLE BusJourney;
    DROP TABLE BusServiceVia;
    DROP TABLE BusService;
    DROP TABLE BusOperator;
    DROP TABLE BusStop;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusTypes ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP TYPE BusStopUserDetails;
    DROP TYPE BusStopLegUserDetails;
    DROP TYPE BusVehicleUserDetails;
    DROP TYPE BusLegUserDetails;
    DROP TYPE BusCallDetails;
    DROP TYPE BusServiceDetails;
    DROP TYPE BusLegUserDetails;
    DROP TYPE BusJourneyDetails;
    DROP TYPE BusJourneyCallDetails;
    DROP TYPE BusCallStopDetails;
    DROP TYPE BusJourneyServiceDetails;
    DROP TYPE BusVehicleDetails;
    DROP TYPE BusOperatorDetails;
    DROP TYPE BusOperatorDetails;
    DROP TYPE BusStopDetails;
    DROP TYPE BusJourneyInData;
    DROP TYPE BusCallInData;
    DROP TYPE BusVehicleInData;
    DROP TYPE BusModelInData;
    DROP TYPE BusServiceViaInData;
    DROP TYPE BusLegInData;
    DROP TYPE BusServiceInData;
    DROP TYPE BusOperatorInData;
    DROP TYPE BusStopInData;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusInsertFunctions ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP FUNCTION InsertBusStops;
    DROP FUNCTION InsertBusOperators;
    DROP FUNCTION InsertBusServices;
    DROP FUNCTION InsertBusServiceVias;
    DROP FUNCTION InsertTransXChangeBusData;
    DROP FUNCTION InsertBusModels;
    DROP FUNCTION InsertBusVehicles;
    DROP FUNCTION InsertBusModelsAndVehicles;
    DROP FUNCTION InsertBusCalls;
    DROP FUNCTION InsertBusJourney;
    DROP FUNCTION InsertBusLeg;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusViews ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP VIEW BusStopLegUserDetailsView;
    DROP VIEW BusVehicleUserDetailsView;
    DROP VIEW BusLegUserDetailsView;
    DROP VIEW BusJourneyDetailsView;
    DROP VIEW BusVehicleDetailsView;
    DROP VIEW BusServiceDetailsView;
    DROP VIEW BusServiceViaData;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusSelectFunctions ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP FUNCTION GetBusStops;
    DROP FUNCTION GetBusStopsByName;
    DROP FUNCTION GetBusStopsByAtco;
    DROP FUNCTION GetBusStopsByJourney;
    DROP FUNCTION GetBusOperators;
    DROP FUNCTION GetBusOperatorsByName;
    DROP FUNCTION GetBusOperatorsByNationalOperatorCode;
    DROP FUNCTION GetBusServices;
    DROP FUNCTION GetBusServicesByOperatorId;
    DROP FUNCTION GetBusServicesByNationalOperatorCode;
    DROP FUNCTION GetBusServicesByOperatorName;
    DROP FUNCTION GetBusVehicles;
    DROP FUNCTION GetUserDetailsForBusStops;
    DROP FUNCTION GetUserDetailsForBusStopByAtco;
    DROP FUNCTION GetUserDetailsForBusStop;
    DROP FUNCTION GetUserDetailsForBusVehicles;
    DROP FUNCTION GetUserDetailsForBusLeg;
    DROP FUNCTION GetUserDetailsForBusLegsByDatetime;
    DROP FUNCTION GetUserDetailsForBusLegsByStartDatetime;
    DROP FUNCTION GetUserDetailsForBusLegsByEndDatetime;
    DROP FUNCTION GetUserDetailsForBusLegsByIds;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusData ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM DropBusSelectFunctions();
    PERFORM DropBusViews();
    PERFORM DropBusInsertFunctions();
    PERFORM DropBusTypes();
    PERFORM DropBusTables();
END;
$$;