from rdkit import Chem

def test_smiles(smiles_string):
    mol = Chem.MolFromSmiles(smiles_string)
    if mol is None:
        raise ValueError("Invalid SMILES string")
    
    wildcard_atoms = [atom for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0]
    if wildcard_atoms:
        print(f"Warning: SMILES contains {len(wildcard_atoms)} wildcard atom(s)")
    
    return mol

smiles = "*C(N)C(=O)O"
test_smiles(smiles)

smiles = "[1*]OC[C@]([H])(COP(=O)([O-])OCC[NH3+])O[2*]"
test_smiles(smiles)