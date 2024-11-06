import { AdvancedMarker, APIProvider, Map } from '@vis.gl/react-google-maps';
import { useEffect, useState } from 'react';

function FilterPanel({ showFilter, filters, setFilters, locations }) {
    const primaryTypeOptions = getUniqueValuesWithCounts(
        locations,
        'song_type_main',
        filters,
        'primary_type'
    );
    const secondaryTypeOptions = getUniqueValuesWithCounts(
        locations,
        'song_type_secondary',
        filters,
        'secondary_type'
    );
    const instrumentOptions = getUniqueValuesWithCounts(
        locations,
        'instrument',
        filters,
        'instrument'
    );
    const collectorOptions = getUniqueValuesWithCounts(
        locations,
        'collector',
        filters,
        'collector'
    );

    return (
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-xl p-4 z-10 w-80">
            <div className="flex flex-col space-y-4">
                <h3 className="font-bold text-lg">Filter</h3>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Titel
                    </label>
                    <input
                        type="text"
                        className="w-full p-2 border rounded-md bg-white"
                        placeholder="Sök på titel..."
                        value={filters.title}
                        onChange={(e) => setFilters({ ...filters, title: e.target.value })}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Primär låttyp
                    </label>
                    <select
                        className="w-full p-2 border rounded-md bg-white"
                        onChange={(e) => setFilters({ ...filters, primary_type: e.target.value })}
                        value={filters.primary_type}
                    >
                        <option value="">Alla</option>
                        {primaryTypeOptions.map(({ value, count }) => (
                            <option key={value} value={value}>
                                {value} ({count})
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Sekundär låttyp
                    </label>
                    <select
                        className="w-full p-2 border rounded-md bg-white"
                        onChange={(e) => setFilters({ ...filters, secondary_type: e.target.value })}
                        value={filters.secondary_type}
                    >
                        <option value="">Alla</option>
                        {secondaryTypeOptions.map(({ value, count }) => (
                            <option key={value} value={value}>
                                {value} ({count})
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Instrument
                    </label>
                    <select
                        className="w-full p-2 border rounded-md bg-white"
                        onChange={(e) => setFilters({ ...filters, instrument: e.target.value })}
                        value={filters.instrument}
                    >
                        <option value="">Alla</option>
                        {instrumentOptions.map(({ value, count }) => (
                            <option key={value} value={value}>
                                {value} ({count})
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Inspelat/inlämnat av
                    </label>
                    <select
                        className="w-full p-2 border rounded-md bg-white"
                        onChange={(e) => setFilters({ ...filters, collector: e.target.value })}
                        value={filters.collector}
                    >
                        <option value="">Alla</option>
                        {collectorOptions.map(({ value, count }) => (
                            <option key={value} value={value}>
                                {value} ({count})
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}

function RecordTable({ records }) {
    return (
        <div className="mt-4 max-h-[80vh] overflow-y-auto">
            <div className="divide-y divide-gray-200">
                {records.map((record, idx) => (
                    <div key={`${record['Acc.nr']}-${record['Låt nr']}-${idx}`} className="py-4">
                        <div className="text-sm text-gray-500">
                            Acc.nr: {record['Acc.nr']} | Låt nr: {record['Låt nr']}
                        </div>
                        <div className="mt-1 grid grid-cols-3 gap-4">
                            <div>
                                <span className="font-semibold">Titel: </span>
                                {record['Titel eller låtnamn']}
                            </div>
                            <div>
                                {record['Låttyp eller visgenre'] && (
                                    <>
                                        <span className="font-semibold">Låttyp: </span>
                                        {record['Låttyp eller visgenre']}
                                    </>
                                )}
                            </div>
                            <div>
                                {record['Sång  instrument'] && (
                                    <>
                                        <span className="font-semibold">Sång/instrument: </span>
                                        {record['Sång  instrument']}
                                    </>
                                )}
                            </div>
                        </div>
                        <div className="mt-1 grid grid-cols-3 gap-4">
                            <div className="col-span-2">
                                {record['Sångare,  Instrumentalist, namn'] && (
                                    <>
                                        <span className="font-semibold">Utövare: </span>
                                        {record['Sångare,  Instrumentalist, namn']}
                                    </>
                                )}
                            </div>
                            <div>
                                {record['Född år'] && (
                                    <>
                                        <span className="font-semibold">Född år: </span>
                                        {record['Född år']}
                                    </>
                                )}
                            </div>
                        </div>
                        <div className="mt-1 grid grid-cols-3 gap-4">
                            <div>
                                {record['Inspelat/ inlämnat av'] && (
                                    <>
                                        <span className="font-semibold">Inlämnat av: </span>
                                        {record['Inspelat/ inlämnat av']}
                                    </>
                                )}
                            </div>
                            <div>
                                {record['Inspelat/nedtecknat år'] && (
                                    <>
                                        <span className="font-semibold">Nedtecknat år: </span>
                                        {record['Inspelat/nedtecknat år']}
                                    </>
                                )}
                            </div>
                            <div>
                                {record['Inspelat år'] && (
                                    <>
                                        <span className="font-semibold">Inspelat år: </span>
                                        {record['Inspelat år']}
                                    </>
                                )}
                            </div>
                        </div>
                        {record["Övrigt"] && (
                            <div className="mt-1">
                                <div>
                                    <span className="font-semibold">Övrigt: </span>
                                    {record['Övrigt']}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

function LocationModal({ location, records, onClose }) {
    const [location_name, landscape] = location.split(" | ");

    // Add this useEffect
    useEffect(() => {
        const handleEscapeKey = (event) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscapeKey);

        // Cleanup function to remove the event listener
        return () => {
            document.removeEventListener('keydown', handleEscapeKey);
        };
    }, [onClose]);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-20">
            <div className="bg-white p-4 rounded-lg shadow-xl w-[98vw] mx-2">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-xl font-bold mb-1">{location_name}</h3>
                        <p className="text-gray-600">{landscape}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Stäng
                    </button>
                </div>

                <RecordTable records={records} />
            </div>
        </div>
    );
}

function TuneMap() {
    const [showFilter, setShowFilter] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [filters, setFilters] = useState({
        title: '',
        primary_type: '',
        secondary_type: '',
        instrument: '',
        collector: ''
    });
    const [locations, setLocations] = useState({});

    useEffect(() => {
        fetch('/hitta.json')
            .then(response => response.json())
            .then(data => setLocations(data))
            .catch(error => console.error('Error loading hitta.json:', error));
    }, []);

    // Filter locations based on current filters
    const filteredLocations = getFilteredLocations(locations, filters);

    // Create one pin per location from filtered locations
    const locationPins = Object.entries(filteredLocations).flatMap(([location, data]) => {
        if (!data.coords) {
            return [];
        }
        return data.coords.map((coord, index) => ({
            id: location + index,
            position: { lat: coord[0], lng: coord[1] },
            location: location,
            data: data
        }));
    });

    function handlePinClick(location, locationData) {
        setSelectedLocation({ location, data: locationData });
        setShowModal(true);
    }

    return (
        <div className="relative w-screen h-screen">
            <div className="w-full h-full">
                <APIProvider apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}>
                    <Map
                        mapId="22e3cdf95b12a2b5"
                        defaultCenter={{ lat: 58.3340403, lng: 12.6802177 }}
                        defaultZoom={8}
                        maxZoom={15}
                        minZoom={6}
                        gestureHandling={'greedy'}
                        className="w-full h-full"
                        disableDefaultUI={true}
                    >
                        {locationPins.map(pin => (
                            <AdvancedMarker
                                key={pin.id}
                                position={pin.position}
                                onClick={() => handlePinClick(pin.location, pin.data)}
                            />
                        ))}
                    </Map>
                </APIProvider>
            </div>

            {showFilter && (
                <FilterPanel
                    showFilter={showFilter}
                    filters={filters}
                    setFilters={setFilters}
                    locations={locations}
                />
            )}

            <button
                onClick={() => setShowFilter(!showFilter)}
                className="absolute right-4 top-4 px-4 py-2 bg-white shadow-lg rounded-md hover:bg-gray-50 z-20"
            >
                {showFilter ? 'Dölj filter' : 'Visa filter'}
            </button>

            {showModal && selectedLocation && (
                <LocationModal
                    location={selectedLocation.location}
                    records={selectedLocation.data.rows}
                    onClose={() => setShowModal(false)}
                />
            )}
        </div>
    );
}

function getUniqueValuesWithCounts(locations, field, filters, excludeField) {
    const counts = {};

    Object.values(locations).forEach(location => {
        location.rows.forEach(row => {
            // Only count rows that match the other filter
            const otherFilters = { ...filters };
            delete otherFilters[excludeField];

            if (filterRows(row, otherFilters)) {
                if (field === 'song_type_main') {
                    if (row.filter && row.filter.song_type && row.filter.song_type.main) {
                        counts[row.filter.song_type.main] =
                            (counts[row.filter.song_type.main] || 0) + 1;
                    }
                } else if (field === 'song_type_secondary') {
                    if (row.filter && row.filter.song_type && row.filter.song_type.secondary) {
                        row.filter.song_type.secondary.forEach(type => {
                            counts[type] = (counts[type] || 0) + 1;
                        });
                    }
                } else if (field === 'instrument') {
                    if (row.filter && row.filter.instrument) {
                        row.filter.instrument.forEach(instrument => {
                            counts[instrument] = (counts[instrument] || 0) + 1;
                        });
                    }
                } else if (field === 'collector') {
                    if (row.filter && row.filter.collector) {
                        counts[row.filter.collector] =
                            (counts[row.filter.collector] || 0) + 1;
                    }
                }
            }
        });
    });

    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .map(([value, count]) => ({ value, count }));
}

function filterRows(row, filters) {
    // Check if row has filter data
    if (!row.filter) return false;

    // Title filtering
    const titleMatch = !filters.title || (
        row['Titel eller låtnamn'] &&
        row['Titel eller låtnamn'].toLowerCase().includes(filters.title.toLowerCase())
    );

    // Primary type filtering
    const primaryTypeMatch = !filters.primary_type || (
        row.filter.song_type &&
        row.filter.song_type.main === filters.primary_type
    );

    // Secondary type filtering
    const secondaryTypeMatch = !filters.secondary_type || (
        row.filter.song_type &&
        row.filter.song_type.secondary &&
        row.filter.song_type.secondary.includes(filters.secondary_type)
    );

    // Instrument filtering
    const instrumentMatch = !filters.instrument || (
        row.filter.instrument &&
        row.filter.instrument.includes(filters.instrument)
    );

    // Collector filtering
    const collectorMatch = !filters.collector || (
        row.filter.collector === filters.collector
    );

    return titleMatch && primaryTypeMatch && secondaryTypeMatch && instrumentMatch && collectorMatch;
}

function getFilteredLocations(locations, filters) {
    return Object.entries(locations).reduce((acc, [location, data]) => {
        const filteredRows = data.rows.filter(row => filterRows(row, filters));
        if (filteredRows.length > 0) {
            acc[location] = {
                ...data,
                rows: filteredRows
            };
        }
        return acc;
    }, {});
}



export default TuneMap;
