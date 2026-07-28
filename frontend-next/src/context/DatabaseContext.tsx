"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface DatabaseFormData {
  type: string;
  host: string;
  port: string;
  username: string;
  password?: string; // Volatile in-memory only
  database: string;
}

export interface TestResult {
  success: boolean;
  message: string;
}

interface DatabaseContextType {
  formData: DatabaseFormData;
  setFormData: React.Dispatch<React.SetStateAction<DatabaseFormData>>;
  selectedTable: string;
  setSelectedTable: React.Dispatch<React.SetStateAction<string>>;
  isTesting: boolean;
  setIsTesting: React.Dispatch<React.SetStateAction<boolean>>;
  isInspecting: boolean;
  setIsInspecting: React.Dispatch<React.SetStateAction<boolean>>;
  isConnected: boolean;
  setIsConnected: React.Dispatch<React.SetStateAction<boolean>>;
  connectedTable: string;
  setConnectedTable: React.Dispatch<React.SetStateAction<string>>;
  testResult: TestResult | null;
  setTestResult: React.Dispatch<React.SetStateAction<TestResult | null>>;
  inspectionData: any;
  setInspectionData: React.Dispatch<React.SetStateAction<any>>;
  inspectionError: string | null;
  setInspectionError: React.Dispatch<React.SetStateAction<string | null>>;
  handleInputChange: (field: string, value: string) => void;
  resetWorkflow: () => void;
}

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

const INITIAL_FORM_DATA: DatabaseFormData = {
  type: 'postgresql',
  host: '',
  port: '',
  username: '',
  password: '',
  database: '',
};

export function DatabaseProvider({ children }: { children: ReactNode }) {
  const [formData, setFormData] = useState<DatabaseFormData>(INITIAL_FORM_DATA);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [isTesting, setIsTesting] = useState(false);
  const [isInspecting, setIsInspecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectedTable, setConnectedTable] = useState<string>('');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [inspectionData, setInspectionData] = useState<any>(null);
  const [inspectionError, setInspectionError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setTestResult(null);
    setInspectionData(null);
    setInspectionError(null);
    setSelectedTable('');
    setIsConnected(false);
    setConnectedTable('');
  };

  const resetWorkflow = () => {
    setFormData(INITIAL_FORM_DATA);
    setSelectedTable('');
    setIsTesting(false);
    setIsInspecting(false);
    setIsConnected(false);
    setConnectedTable('');
    setTestResult(null);
    setInspectionData(null);
    setInspectionError(null);
  };

  return (
    <DatabaseContext.Provider
      value={{
        formData,
        setFormData,
        selectedTable,
        setSelectedTable,
        isTesting,
        setIsTesting,
        isInspecting,
        setIsInspecting,
        isConnected,
        setIsConnected,
        connectedTable,
        setConnectedTable,
        testResult,
        setTestResult,
        inspectionData,
        setInspectionData,
        inspectionError,
        setInspectionError,
        handleInputChange,
        resetWorkflow,
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
}

export function useDatabase() {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error('useDatabase must be used within a DatabaseProvider');
  }
  return context;
}

export const useDatabaseContext = useDatabase;
