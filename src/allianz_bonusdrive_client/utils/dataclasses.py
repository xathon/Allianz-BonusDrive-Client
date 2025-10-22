from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")

@dataclass
class Trip:
    events: Optional["Events"]
    tripId: str
    tripStartTimestampUtc: int
    tripEndTimestampUtc: int
    tripStartTimestampLocal: int
    tripEndTimestampLocal: int
    tripProcessingEndTimestampUtc: int
    kilometers: float
    avgKilometersPerHour: float
    maxKilometersPerHour: float
    seconds: int
    secondsOfIdling: int
    timeZoneOffsetMillis: int
    tripStatus: str
    pois: Optional[List]
    transportMode: str
    transportModeMessageKey: str
    transportModeReason: Optional[str]
    geometry: str
    snappedGeometry: List["SnappedGeometry"]
    reconstructedStartGeometry: str
    tripStartStatus: str
    verified: bool
    hasAlerts: bool
    alerts: Optional[List]
    vehicle: "Vehicle"
    user: "User"
    device: Optional[str]
    tripScores: "TripScores"
    milStatus: Optional[str]
    dtcCount: Optional[str]
    tripScore: float
    eventsCount: int
    private: bool
    tripUUID: str
    purpose: str
    # if geometry was decoded:
    decoded_geometry: Optional[List[tuple[float, float]]]
    start_point_string: Optional[str]
    end_point_string: Optional[str]


@dataclass
class EventData(Generic[T]):
    latitude: float
    longitude: float
    timeStamp: int
    level: int
    kmPerHour: float
    averageKmPerHour: Optional[T]
    geometry: str
    secondsOfDriving: Optional[T]
    kmSpeedLimit: Optional[T]
    timeZoneOffsetMillis: int
    transportMode: str

@dataclass
class Events(Generic[T]):
    MultiLevelAccelerationViolation: Optional[List[EventData[T]]]
    MultiLevelBrakingViolation: Optional[List[EventData[T]]]
    MultiLevelCorneringViolation: Optional[List[EventData[T]]]
    PostedSpeedLimitViolation: Optional[List[EventData[T]]]

@dataclass
class SnappedGeometry:
    startTimestamp: int
    endTimestamp: int
    geometry: str
    confidence: float
    unsnappableRatio: float

@dataclass
class Vehicle:
    vehicleId: str
    make: str
    model: str
    nickname: Optional[str]
    year: Optional[int]
    plate: Optional[str]
    avatar: Optional[str]
    accountId: Optional[str]
    accountNumber: Optional[str]
    policyInceptionDate: Optional[int]
    policyStartDate: Optional[int]
    extraAccountId: Optional[str]
    extraAccountNumber: Optional[str]

@dataclass
class User:
    userId: str
    publicDisplayName: str
    avatar: Optional[str]
    sharedInformation: Optional[str]
    associatedUsers: Optional[List]
    account: Optional[str]
    userRole: Optional[str]
    accountRole: Optional[str]
    firstName: str
    lastName: str

@dataclass
class TripScores:
    scores: "Scores"
    scoreType: int

@dataclass
class Scores:
    over_speeding: float
    speeding: float
    distracted_driving: float
    payd: float
    overall: float
    harsh_cornering: float
    harsh_acceleration: float
    harsh_braking: float
    mileage: float

@dataclass
class Badge:
    badgeType: str
    level: int
    pointsAwarded: int
    date: int
    state: str
    usedBadgeLevels: Optional[List["BadgeLevel"]]

@dataclass
class BadgeLevel:
    level: int
    minimumValue: float
    maximumValue: float