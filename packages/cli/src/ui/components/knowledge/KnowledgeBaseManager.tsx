import React, { useState } from 'react';
import { DocumentBrowser } from './DocumentBrowser.js';
import { SearchInterface } from './SearchInterface.js';
import { IngestionWorkflow } from './IngestionWorkflow.js';
import { KnowledgeDocument } from '../../knowledge/types.js';
import { Box, Text } from 'ink';

export const KnowledgeBaseManager: React.FC = () => {
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocument | null>(null);

  const handleDocumentSelect = (document: KnowledgeDocument) => {
    setSelectedDocument(document);
  };

  return (
    <Box flexDirection="column">
      <Text>Knowledge Base Manager</Text>
      <SearchInterface onDocumentSelect={handleDocumentSelect} />
      <DocumentBrowser selectedDocument={selectedDocument} />
      <IngestionWorkflow />
    </Box>
  );
};
