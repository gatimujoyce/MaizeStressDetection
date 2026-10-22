import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useFarmerFarms } from '../api/hooks'

const SELECTED_FARM_KEY = 'msm_selected_farm'
const FarmContext = createContext(null)

function readSelectedFarmId() {
  try {
    return localStorage.getItem(SELECTED_FARM_KEY)
  } catch (error) {
    console.error('Unable to read saved farm selection', error)
    return null
  }
}

function storeSelectedFarmId(farmId) {
  try {
    localStorage.setItem(SELECTED_FARM_KEY, farmId)
  } catch (error) {
    console.error('Unable to save selected farm', error)
    return
  }
}

export function FarmProvider({ children }) {
  const { role, userId } = useAuth()
  const isFarmer = role === 'farmer'
  const farmsQuery = useFarmerFarms(isFarmer ? userId : null)
  const farms = useMemo(
    () => isFarmer ? farmsQuery.data ?? [] : [],
    [isFarmer, farmsQuery.data]
  )
  const isLoading = isFarmer && farmsQuery.isLoading
  const hasFarms = farms.length > 0
  const [preferredFarmId, setPreferredFarmId] = useState(readSelectedFarmId)
  const selectedFarmId = farms.some((farm) => farm.farm_id === preferredFarmId)
    ? preferredFarmId
    : farms[0]?.farm_id ?? null
  const selectedFarm = farms.find((farm) => farm.farm_id === selectedFarmId) ?? null

  const selectFarm = useCallback((farmId) => {
    if (!farmId) return
    setPreferredFarmId(farmId)
    storeSelectedFarmId(farmId)
  }, [])

  return (
    <FarmContext.Provider
      value={{ farms, selectedFarm, selectedFarmId, selectFarm, isLoading, hasFarms }}
    >
      {children}
    </FarmContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useFarm() {
  const context = useContext(FarmContext)
  if (!context) throw new Error('useFarm must be used within a FarmProvider')
  return context
}
